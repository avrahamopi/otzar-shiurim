"""Write podcast RSS feeds into dist/feeds/ from data/shiurim.json.

Feeds: all.xml, one per topic, one per yeshiva, one per rabbi with enough
audio shiurim. Only shiurim with an audio file ("a") go into a feed; each
episode points at the yeshiva's original MP3 (nothing is re-hosted).
Also writes dist/feeds/index.json, which the site uses for its podcast menu.
"""
import json, hashlib, pathlib, datetime
from email.utils import format_datetime
from xml.sax.saxutils import escape

root = pathlib.Path(__file__).parent.parent
cfg = json.loads((root / "data/feeds_config.json").read_text(encoding="utf-8"))
yeshivot = {y["id"]: y for y in json.loads((root / "data/yeshivot.json").read_text(encoding="utf-8"))}
shiurim = [s for s in json.loads((root / "data/shiurim.json").read_text(encoding="utf-8")) if s.get("a")]
out = root / "dist/feeds"
out.mkdir(parents=True, exist_ok=True)
SITE = cfg["site_url"].rstrip("/")
COVER = f"{SITE}/feeds/cover.jpg"

TOPIC_SLUG = {"גמרא": "gemara", "הלכה": "halacha", 'תנ"ך': "tanach", "פרשת השבוע": "parasha",
              "אמונה ומחשבה": "emuna", "מוסר": "musar", "חסידות וקבלה": "chasidut", "מועדים": "moadim"}


def rabbi_slug(name):
    return "rav-" + hashlib.sha1(name.encode()).hexdigest()[:8]


def pubdate(d):
    dt = datetime.datetime.fromisoformat(d).replace(hour=12, tzinfo=datetime.timezone.utc)
    return format_datetime(dt)


def item(s):
    y = yeshivot.get(s["y"], {"n": s["y"]})
    rabbi = s.get("r") or "רבני הישיבה"
    desc = f'{rabbi} · ישיבת {y["n"]} · {s["c"]}'
    if s.get("v"):
        desc += f'\nוידאו: https://www.youtube.com/watch?v={s["v"]}'
    dur = f'<itunes:duration>{s["d"] * 60}</itunes:duration>' if s.get("d") else ""
    return f"""  <item>
   <title>{escape(s["t"])}</title>
   <description>{escape(desc)}</description>
   <itunes:author>{escape(rabbi)}</itunes:author>
   <enclosure url="{escape(s["a"])}" length="0" type="audio/mpeg"/>
   <guid isPermaLink="false">{escape(s["a"])}</guid>
   <pubDate>{pubdate(s["dt"])}</pubDate>
   {dur}<itunes:explicit>false</itunes:explicit>
  </item>"""


def feed(slug, title, desc, items):
    items = sorted(items, key=lambda s: s["dt"], reverse=True)
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom">
 <channel>
  <title>{escape(title)}</title>
  <link>{SITE}/</link>
  <atom:link href="{SITE}/feeds/{slug}.xml" rel="self" type="application/rss+xml"/>
  <language>{cfg["language"]}</language>
  <description>{escape(desc)}</description>
  <itunes:author>{escape(cfg["author"])}</itunes:author>
  <itunes:owner><itunes:name>{escape(cfg["owner_name"])}</itunes:name><itunes:email>{escape(cfg["owner_email"])}</itunes:email></itunes:owner>
  <itunes:image href="{COVER}"/>
  <itunes:category text="Religion &amp; Spirituality"><itunes:category text="Judaism"/></itunes:category>
  <itunes:explicit>false</itunes:explicit>
  <itunes:type>episodic</itunes:type>
{chr(10).join(item(s) for s in items)}
 </channel>
</rss>
"""
    (out / f"{slug}.xml").write_text(xml, encoding="utf-8")
    return {"slug": slug, "title": title, "n": len(items), "url": f"{SITE}/feeds/{slug}.xml"}


index = [feed("all", cfg["title"], cfg["description"], shiurim)]
for topic, slug in TOPIC_SLUG.items():
    its = [s for s in shiurim if s["c"] == topic]
    if its:
        f = feed(slug, f'{topic} · {cfg["title"]}', f'שיעורי {topic} מכל ישיבות ההסדר.', its)
        f.update(kind="topic", key=topic)
        index.append(f)
for yid in sorted({s["y"] for s in shiurim}):
    its = [s for s in shiurim if s["y"] == yid]
    name = yeshivot.get(yid, {"n": yid})["n"]
    f = feed(f"y-{yid}", f"ישיבת {name} · {cfg['title']}", f"שיעורי ישיבת {name}.", its)
    f.update(kind="yeshiva", key=yid)
    index.append(f)
for rabbi in sorted({s.get("r") for s in shiurim if s.get("r")}):
    its = [s for s in shiurim if s.get("r") == rabbi]
    if len(its) >= cfg["min_rabbi_feed"]:
        f = feed(rabbi_slug(rabbi), f"{rabbi} · {cfg['title']}", f"שיעורי {rabbi}.", its)
        f.update(kind="rabbi", key=rabbi)
        index.append(f)
index[0].update(kind="all", key="")
(out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{len(index)} feeds, {len(shiurim)} audio shiurim")
for f in index:
    print(f'  {f["slug"]:16} {f["n"]:3}  {f["title"]}')
