"""Pull new shiurim (audio + video) from every yeshiva into data/shiurim.json.

Audio comes from each yeshiva's podcast RSS feed (direct MP3 files, meant for
playback in any app). Video comes from the YouTube channel. When the same
shiur appears in both, they are merged into one entry with both "a" and "v".

Run on any machine with normal internet (a server, GitHub Actions, your laptop):
    python3 ingest/ingest.py

No API key needed: it reads each channel's public RSS feed
(https://www.youtube.com/feeds/videos.xml?channel_id=...), which lists the
latest 15 videos. Run it every few hours and the site stays current.
Durations are not in the RSS feed; set YT_API_KEY to fill them in through the
YouTube Data API (videos.list, 1 quota unit per 50 videos).
"""
import json, os, pathlib, re, sys, urllib.error, urllib.request, urllib.parse
import xml.etree.ElementTree as ET

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from tagger import tag, find_rabbi

DATA = pathlib.Path(__file__).parent.parent / "data"
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
UA = {"User-Agent": "Mozilla/5.0 (shiurim-aggregator)", "Accept-Language": "he"}
SKIP = re.compile(r"קמפיין|תרומה|להרשמה|שיר |ניגון|קליפ|#shorts", re.I)


def get(url):
    url = urllib.parse.quote(url, safe=":/?&=%#+,;@!$'()*~")  # Hebrew paths -> %xx
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def channel_id(ref):
    """Accept 'UC…' or '@handle' and return the UC… channel id."""
    if ref.startswith("UC"):
        return ref
    html = get(f"https://www.youtube.com/{ref}")
    m = re.search(r'"channelId":"(UC[\w-]{22})"', html) or re.search(r'channel/(UC[\w-]{22})', html)
    if not m:
        raise ValueError(f"no channel id for {ref}")
    return m.group(1)


def feed(cid):
    root = ET.fromstring(get(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"))
    for e in root.findall("a:entry", NS):
        link = e.find("a:link", NS).get("href", "")
        if "/shorts/" in link:
            continue
        yield {
            "v": e.find("yt:videoId", NS).text,
            "title": e.find("a:title", NS).text or "",
            "dt": (e.find("a:published", NS).text or "")[:10],
        }


def durations(ids, key):
    out = {}
    for i in range(0, len(ids), 50):
        q = urllib.parse.urlencode({"part": "contentDetails", "id": ",".join(ids[i:i + 50]), "key": key})
        for it in json.loads(get(f"https://www.googleapis.com/youtube/v3/videos?{q}"))["items"]:
            m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", it["contentDetails"]["duration"])
            h, mi, s = (int(x or 0) for x in m.groups())
            out[it["id"]] = max(1, round(h * 60 + mi + s / 60))
    return out


# ---------- audio: podcast feeds (the site's main listening source) ----------
ITUNES = "http://www.itunes.com/dtds/podcast-1.0.dtd"


def podcast_feed_url(ref):
    """Accept a feed URL or an Apple Podcasts id (digits) and return the RSS URL."""
    if ref.startswith("http"):
        return ref
    data = json.loads(get(f"https://itunes.apple.com/lookup?id={ref}"))
    return data["results"][0]["feedUrl"]


def podcast(ref, meta=None):
    """Yield episodes of one podcast feed. If meta is a dict, it receives the show's
    title and author (used as series name and as a fallback for the rabbi)."""
    root = ET.fromstring(get(podcast_feed_url(ref)).encode("utf-8"))
    from email.utils import parsedate_to_datetime
    chan = root.find("channel")
    if meta is not None and chan is not None:
        meta["title"] = (chan.findtext("title") or "").strip()
        meta["author"] = (chan.findtext(f"{{{ITUNES}}}author") or "").strip()
    for it in root.iter("item"):
        enc = it.find("enclosure")
        if enc is None or not enc.get("url"):
            continue
        dur = it.findtext(f"{{{ITUNES}}}duration") or ""
        mins = None
        if dur:
            parts = [int(x) for x in dur.split(":") if x.isdigit()]
            secs = 0
            for x in parts:
                secs = secs * 60 + x
            mins = max(1, round(secs / 60)) if secs else None
        try:
            dt = parsedate_to_datetime(it.findtext("pubDate")).date().isoformat()
        except Exception:
            dt = ""
        yield {"a": enc.get("url"), "title": it.findtext("title") or "", "dt": dt, "d": mins,
               "guid": it.findtext("guid") or enc.get("url")}


# ---------- audio: yeshiva websites built on WordPress (e.g. sderot.org) ----------
AUDIO_RE = re.compile(r'<audio[^>]+src="([^"]+\.(?:mp3|m4a|ogg)[^"]*)"|href="([^"]+\.mp3)"', re.I)
YT_ID = re.compile(r"/([\w-]{11})\.mp3$")


def wordpress(base, ptype="lessons", max_pages=200):
    """Yield every lesson with an audio file from a WordPress REST API.
    Pages through /wp-json/wp/v2/<ptype>?per_page=100 until the archive ends."""
    import html
    for page in range(1, max_pages + 1):
        q = f"{base}/wp-json/wp/v2/{ptype}?per_page=100&page={page}&_fields=id,date,title,content,link"
        try:
            items = json.loads(get(q))
        except urllib.error.HTTPError as ex:   # past the last page WordPress answers 400
            if ex.code == 400:
                return
            raise
        if not items:
            return
        for it in items:
            m = AUDIO_RE.search(it["content"]["rendered"])
            if not m:
                continue
            a = m.group(1) or m.group(2)
            yt = YT_ID.search(a)
            yield {"a": a, "v": yt.group(1) if yt else None,
                   "title": html.unescape(it["title"]["rendered"]),
                   "dt": it["date"][:10], "id": f"{base}#{it['id']}", "link": it.get("link")}


# ---------- Rav Druckman's legacy site (haravdrukman.co.il) ----------
# Structure: category pages -> series pages (may have /page/N) -> part pages.
# A part page holds a YouTube embed, a Google Drive MP3 link, "שנה:" and "זמן שיעור:".
from html.parser import HTMLParser

DRUKMAN_START = ["מתורתו_של_רבינו"]
GEM = {"א": 1, "ב": 2, "ג": 3, "ד": 4, "ה": 5, "ו": 6, "ז": 7, "ח": 8, "ט": 9, "י": 10, "כ": 20, "ל": 30,
       "מ": 40, "נ": 50, "ס": 60, "ע": 70, "פ": 80, "צ": 90, "ק": 100, "ר": 200, "ש": 300, "ת": 400}


def hebrew_year_to_date(yr):
    """'תשע"ז' -> '2016-10-01' (start of that Jewish year, close enough for sorting)."""
    v = sum(GEM.get(ch, 0) for ch in yr)
    if not v:
        return ""
    return f"{v + 5000 - 3761}-10-01"


class MainLinks(HTMLParser):
    """Collect hrefs that appear inside <main> (skips menus and footer)."""
    def __init__(self):
        super().__init__()
        self.depth, self.links, self.h1, self._in_h1 = 0, [], [], False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "main":
            self.depth += 1
        if tag == "a" and self.depth and a.get("href"):
            self.links.append(a["href"])
        if tag == "h1":
            self._in_h1 = True
            self.h1.append("")
    def handle_endtag(self, tag):
        if tag == "main":
            self.depth -= 1
        if tag == "h1":
            self._in_h1 = False
    def handle_data(self, d):
        if self._in_h1:
            self.h1[-1] += d


def drukman(base, max_pages=800, skip=frozenset()):
    import html, time
    base = base.rstrip("/")
    seen, queue, pages = set(skip), [f"{base}/{p}" for p in DRUKMAN_START], 0
    while queue and pages < max_pages:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        try:
            page = get(url)
        except Exception:
            continue
        pages += 1
        time.sleep(0.3)  # be polite to the yeshiva's server
        drive = re.search(r"drive\.google\.com/file/d/([\w-]{20,})", page)
        if drive:  # a lesson part
            p = MainLinks(); p.feed(page)
            title = html.unescape((p.h1[-1] if p.h1 else "").strip())
            yt = re.search(r"youtube(?:-nocookie)?\.com/embed/([\w-]{11})", page)
            yr = re.search(r"שנה:\s*([^<\n]+)", page)
            dur = re.search(r"זמן שיעור:\s*(\d+)", page)
            yr = yr.group(1).strip().strip('"') if yr else ""
            yield {"a": f"https://drive.usercontent.google.com/download?export=download&id={drive.group(1)}",
                   "v": yt.group(1) if yt else None, "title": title, "yr": yr,
                   "dt": hebrew_year_to_date(yr), "d": int(dur.group(1)) if dur else None, "link": url}
            continue
        p = MainLinks(); p.feed(page)
        for h in p.links:
            h = urllib.parse.urljoin(url, h).split("#")[0]
            if h.startswith(base) and h not in seen and not h.endswith((".pdf", ".jpg", ".png")):
                queue.append(h)



# ---------- audio: generic site crawler (sites with MP3 links on lesson pages) ----------
MP3_RE = re.compile(r"""(?:href|src)=["']([^"']+?\.(?:mp3|m4a))["']""", re.I)
TITLE_RE = re.compile(r"<h1[^>]*>(.*?)</h1>|<title>(.*?)</title>", re.S | re.I)
HREF_RE = re.compile(r"""href=["']([^"'#]+)["']""", re.I)


def crawl(cfg, skip=frozenset()):
    """Breadth-first crawl of one yeshiva site. cfg = {"start": [urls], "follow": regex,
    "max_pages": n}. Yields one shiur per page that links an audio file."""
    import html, time
    follow = re.compile(cfg["follow"])
    host = urllib.parse.urlparse(cfg["start"][0]).netloc
    queue, seen, n = list(cfg["start"]), set(cfg["start"]), 0
    # bounded per run; lesson pages already ingested are skipped, so each run reaches further
    while queue and n < cfg.get("max_pages", 600):
        url = queue.pop(0)
        if url in skip:  # lesson page already ingested on an earlier run
            continue
        n += 1
        try:
            body = get(url)
        except Exception:
            continue
        for h in HREF_RE.findall(body):
            u = urllib.parse.urljoin(url, html.unescape(h))
            if urllib.parse.urlparse(u).netloc == host and u not in seen and follow.search(urllib.parse.unquote(u)):
                seen.add(u); queue.append(u)
        mp3 = list(dict.fromkeys(MP3_RE.findall(body)))
        if len(mp3) > 1:  # a listing page, or a lesson page with a sidebar: keep the file named after this page's id
            pid = re.search(r"[?&]id=(\d+)", url)
            mp3 = [m for m in mp3 if pid and re.search(rf"/{pid.group(1)}\.(?:mp3|m4a)$", m)]
        if mp3:
            m = TITLE_RE.search(body)
            title = re.sub(r"<[^>]+>|\s+", " ", html.unescape(next(g for g in m.groups() if g) if m else "")).strip()
            title = re.split(r"\s[|\-–]\s(?:ישיבת|Yeshiv)", title)[0].strip()
            a = urllib.parse.quote(urllib.parse.urljoin(url, html.unescape(mp3[0])), safe=":/?&=%")
            yield {"a": a, "title": title, "link": url, "dt": "", "v": None}
        time.sleep(0.1)

def _words(t):
    return set(re.findall(r"[א-ת\w]{2,}", re.sub(r'["\'״׳]', "", t)))


def same_shiur(a, b):
    """True when a podcast episode and a YouTube video are the same shiur."""
    wa, wb = _words(a["t"]), _words(b["t"])
    if not wa or not wb:
        return False
    return len(wa & wb) / len(wa | wb) >= 0.6


def main():
    channels = json.loads((DATA / "channels.json").read_text(encoding="utf-8"))
    path = DATA / "shiurim.json"
    known = {s["v"]: s for s in json.loads(path.read_text(encoding="utf-8"))} if path.exists() else {}
    new = []
    # re-tag rabbis with the current rules (cheap, and fixes older entries in place);
    # a podcast's series title ("... | הרב X") names the speaker more reliably than the episode title
    for s_ in known.values():
        if s_.get("r") == "הרב חיים דרוקמן":
            continue
        r = (find_rabbi(s_["sr"]) if s_.get("sr") else "") or find_rabbi(s_["t"])
        s_["r"] = r or "רבני הישיבה"
    for yid, c in channels.items():
        if yid.startswith("_") or not c.get("youtube"):
            continue
        try:
            cid = channel_id(c["youtube"])
            for item in feed(cid):
                if item["v"] in known or SKIP.search(item["title"]):
                    continue
                s = tag(item["title"])
                s.update({"y": yid, "v": item["v"], "d": None, "dt": item["dt"]})
                known[item["v"]] = s
                new.append(s)
            print(f"ok   {yid}")
        except Exception as ex:  # one broken channel must not stop the rest
            print(f"FAIL {yid}: {ex}")
    # audio: attach each podcast episode to its video, or add it as an audio-only shiur
    have_audio = {s["a"] for s in known.values() if s.get("a")}
    for yid, c in channels.items():
        if yid.startswith("_"):
            continue
        feeds = list(c.get("podcasts") or []) + ([c["podcast"]] if c.get("podcast") else [])
        if not feeds:
            continue
        videos = [v for v in known.values() if v["y"] == yid and not v.get("a")]
        added = 0
        for ref in feeds:
            meta = {}
            try:
                for ep in podcast(ref, meta):
                    if ep["a"] in have_audio:
                        continue
                    have_audio.add(ep["a"])
                    s = tag(ep["title"])
                    s["r"] = find_rabbi(meta.get("title", "")) or s["r"] or find_rabbi(meta.get("author", "")) or "רבני הישיבה"
                    twin = next((v for v in videos if not v.get("a") and same_shiur(v, s)), None)
                    if twin:
                        twin["a"] = ep["a"]
                        twin["d"] = twin.get("d") or ep["d"]
                        continue
                    s.update({"y": yid, "v": None, "a": ep["a"], "d": ep["d"], "dt": ep["dt"], "id": ep["guid"]})
                    if meta.get("title"):
                        s["sr"] = meta["title"][:80]
                    known[ep["guid"]] = s
                    new.append(s)
                    added += 1
            except Exception as ex:
                print(f"FAIL {yid} podcast {ref}: {ex}")
        print(f"ok   {yid} (podcasts: {len(feeds)} feeds, {added} new episodes)")
    for yid, c in channels.items():
        if yid.startswith("_") or not c.get("wordpress"):
            continue
        try:
            n = 0
            for les in wordpress(c["wordpress"], c.get("wp_type", "lessons")):
                if les["a"] in have_audio:
                    continue
                s = tag(les["title"])
                twin = known.get(les["v"]) if les["v"] else None
                if twin and not twin.get("a"):
                    twin["a"] = les["a"]
                    continue
                s.update({"y": yid, "v": les["v"], "a": les["a"], "d": None, "dt": les["dt"], "src": les["link"]})
                known[les["id"]] = s
                have_audio.add(les["a"])
                new.append(s)
                n += 1
            print(f"ok   {yid} (site: {n} new)")
        except Exception as ex:
            print(f"FAIL {yid} site: {ex}")
    for yid, c in channels.items():
        if yid.startswith("_") or not c.get("crawl"):
            continue
        n = 0
        try:
            done = {s_.get("src") for s_ in known.values() if s_.get("y") == yid and s_.get("src")}
            for les in crawl(c["crawl"], done):
                if les["a"] in have_audio or not les["title"]:
                    continue
                s = tag(les["title"])
                s["r"] = s["r"] or "רבני הישיבה"
                s.update({"y": yid, "v": None, "a": les["a"], "d": None, "dt": les["dt"], "src": les["link"]})
                known[les["a"]] = s
                have_audio.add(les["a"])
                new.append(s)
                n += 1
            print(f"ok   {yid} (crawl: {n} new)")
        except Exception as ex:
            print(f"FAIL {yid} crawl: {ex}")
    for yid, c in channels.items():
        if yid.startswith("_") or not c.get("drukman"):
            continue
        try:
            n = 0
            done = {s_.get("src") for s_ in known.values() if s_.get("y") == yid and s_.get("src")}
            for les in drukman(c["drukman"], skip=done):
                if les["a"] in have_audio:
                    continue
                twin = known.get(les["v"]) if les["v"] else None
                if twin:  # same shiur already came in from YouTube: give it the audio
                    twin.update({"a": les["a"], "d": twin.get("d") or les["d"], "yr": les["yr"]})
                    continue
                s = tag(les["title"])
                s.update({"y": yid, "r": "הרב חיים דרוקמן", "v": les["v"], "a": les["a"], "d": les["d"],
                          "dt": les["dt"], "yr": les["yr"], "src": les["link"]})
                known[les["a"]] = s
                have_audio.add(les["a"])
                new.append(s)
                n += 1
            print(f"ok   {yid} (drukman: {n} new)")
        except Exception as ex:
            print(f"FAIL {yid} drukman: {ex}")
    key = os.environ.get("YT_API_KEY")
    if key and new:
        d = durations([s["v"] for s in new if s.get("v")], key)
        for s in new:
            s["d"] = d.get(s["v"])
    all_s = sorted(known.values(), key=lambda s: s["dt"], reverse=True)
    path.write_text(json.dumps(all_s, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"{len(new)} new, {len(all_s)} total")


if __name__ == "__main__":
    main()
