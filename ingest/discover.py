"""Find audio sources for every hesder yeshiva. Runs on GitHub Actions (open internet).

For each yeshiva in data/yeshivot.json it collects:
  - podcasts from the Apple Podcasts search API (name, author, feed URL, episode count)
  - the yeshiva's own website (from its hesder.org.il page), and on that site:
      RSS/Atom feeds, WordPress REST post types, audio file links (.mp3/.m4a),
      links to podcast platforms and YouTube
Writes data/discovery.json. Nothing here is added to the site automatically:
a person reviews the matches first (podcast search returns false positives).
"""
import json, re, sys, time, urllib.parse, urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (otzar-shiurim discovery; +https://avrahamopi.github.io/otzar-shiurim/)"
SKIP_HOSTS = ("hesder.org.il", "facebook.com", "instagram.com", "twitter.com", "x.com", "wa.me",
              "whatsapp.com", "google.com", "goo.gl", "waze.com", "linkedin.com", "tiktok.com",
              "gov.il", "w3.org", "wordpress.org", "elementor.com", "wix.com", "schema.org")
PLATFORMS = ("spotify.com", "podcasts.apple.com", "anchor.fm", "buzzsprout", "podbean", "soundcloud",
             "castbox", "pocketcasts", "simplecast", "transistor.fm", "rss.com", "redcircle", "spreaker",
             "youtube.com", "youtu.be", "kol-halashon", "kolhalashon", "yeshiva.org.il", "torahanytime",
             "meirtv", "etzion.org.il", "drive.google.com", "archive.org", "podcastim", "yutorah")
AUDIO_RE = re.compile(r"""https?://[^\s"'<>]+?\.(?:mp3|m4a|aac|ogg|wav)(?:\?[^\s"'<>]*)?""", re.I)


def get(url, timeout=25, limit=3_000_000):
    url = urllib.parse.quote(url, safe=":/?&=%#+,;@~!$*'()")
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "he,en"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.geturl(), r.headers.get("Content-Type", ""), r.read(limit).decode("utf-8", "replace")


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.a = []; self.feeds = []; self.title = ""; self._t = False
    def handle_starttag(self, tag, at):
        d = dict(at)
        if tag == "a" and d.get("href"): self.a.append((d["href"], ""))
        if tag in ("audio", "source") and d.get("src"): self.a.append((d["src"], "audio"))
        if tag == "link" and d.get("href") and any(t in (d.get("type") or "") for t in ("rss", "atom")):
            self.feeds.append(d["href"])
        if tag == "title": self._t = True
    def handle_endtag(self, tag):
        if tag == "title": self._t = False
    def handle_data(self, data):
        if self._t: self.title += data


def host(u):
    return urllib.parse.urlparse(u).netloc.lower().removeprefix("www.")


def itunes(term):
    q = urllib.parse.urlencode({"term": term, "media": "podcast", "country": "IL", "limit": 25})
    try:
        _, _, body = get("https://itunes.apple.com/search?" + q)
        return [{"id": r.get("collectionId"), "name": r.get("collectionName"), "author": r.get("artistName"),
                 "feed": r.get("feedUrl"), "count": r.get("trackCount"), "genre": r.get("primaryGenreName")}
                for r in json.loads(body).get("results", [])]
    except Exception as e:
        return [{"error": str(e)}]


def scan_site(url):
    out = {"url": url}
    try:
        final, ctype, body = get(url)
    except Exception as e:
        out["error"] = str(e); return out
    out["final"] = final
    p = Links(); p.feed(body)
    out["title"] = p.title.strip()[:120]
    base = final
    links = [(urllib.parse.urljoin(base, h), k) for h, k in p.a]
    out["feeds"] = sorted({urllib.parse.urljoin(base, f) for f in p.feeds})
    out["audio"] = sorted({u for u, _ in links if AUDIO_RE.match(u)} | set(AUDIO_RE.findall(body)))[:40]
    out["platforms"] = sorted({u for u, _ in links if any(x in u for x in PLATFORMS)})[:40]
    h = host(final)
    inner = [u for u, _ in links if host(u) == h]
    out["lesson_pages"] = sorted({u for u in inner if re.search(
        r"shiur|lesson|lecture|audio|podcast|media|torah|שיעור|שיעורים|תורה|האזנה|ספרי", urllib.parse.unquote(u), re.I)})[:60]
    # WordPress REST: which post types exist?
    if "wp-content" in body or "wp-json" in body:
        try:
            root = urllib.parse.urlsplit(final)._replace(path="/wp-json/wp/v2/types", query="").geturl()
            _, _, tj = get(root)
            out["wp_types"] = {k: v.get("rest_base") for k, v in json.loads(tj).items()}
        except Exception as e:
            out["wp_types_error"] = str(e)
    return out


def hesder_links(slug):
    url = "https://hesder.org.il/institute/" + slug
    try:
        final, _, body = get(url)
    except Exception as e:
        return {"error": str(e)}
    p = Links(); p.feed(body)
    ext = []
    for h, _ in p.a:
        u = urllib.parse.urljoin(final, h)
        if u.startswith("http") and not any(s in host(u) for s in SKIP_HOSTS):
            ext.append(u)
    return {"external": sorted(set(ext))}


def main():
    ys = json.loads((ROOT / "data/yeshivot.json").read_text())
    extra = json.loads((ROOT / "data/known_sites.json").read_text()) if (ROOT / "data/known_sites.json").exists() else {}
    only = set(sys.argv[1:])
    res = {}
    for y in ys:
        if only and y["id"] not in only: continue
        name = y["n"].split("–")[0].strip()
        terms = {f"ישיבת {name}", f"ישיבת {y['n']}"}
        pods = []
        for t in terms:
            pods += itunes(t); time.sleep(1.2)
        seen = set(); pods = [p for p in pods if p.get("id") not in seen and not seen.add(p.get("id"))]
        hz = hesder_links(urllib.parse.quote(y["h"]))
        sites = list(dict.fromkeys(extra.get(y["id"], []) + [u for u in hz.get("external", [])
                     if not any(x in u for x in PLATFORMS)]))[:4]
        res[y["id"]] = {"name": y["n"], "podcasts": pods, "hesder": hz,
                        "sites": [scan_site(u) for u in sites]}
        print(y["id"], len(pods), "podcasts,", len(sites), "sites", flush=True)
    out = ROOT / "data/discovery.json"
    old = json.loads(out.read_text()) if out.exists() and only else {}
    old.update(res)
    out.write_text(json.dumps(old, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
