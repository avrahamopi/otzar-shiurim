"""Second pass: search Apple Podcasts broadly (limit 200) for every hesder yeshiva's
author strings, then attribute each podcast to a yeshiva by data/pod_match.json.
Writes data/podcasts_found.json for review."""
import json, time, urllib.parse, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
M = json.loads((ROOT / "data/pod_match.json").read_text())

def search(term):
    q = urllib.parse.urlencode({"term": term, "media": "podcast", "country": "IL", "limit": 200})
    req = urllib.request.Request("https://itunes.apple.com/search?" + q, headers={"User-Agent": "Mozilla/5.0"})
    for i in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read()).get("results", [])
        except Exception as e:
            time.sleep(5 * (i + 1))
    return []

found = {}
terms = sorted({t for v in M["yeshivot"].values() for t in v} | set(M.get("extra_terms", [])))
for t in terms:
    for r in search(t):
        if r.get("feedUrl"):
            found[r["collectionId"]] = {"id": r["collectionId"], "name": r.get("collectionName", ""),
                "author": r.get("artistName", ""), "feed": r["feedUrl"], "count": r.get("trackCount", 0)}
    time.sleep(2.5)
    print(t, len(found), flush=True)

def who(p):
    hay = (p["author"] + " | " + p["name"]).lower()
    if any(x.lower() in hay for x in M["exclude"]): return None
    hits = [y for y, pats in M["yeshivot"].items() if any(x.lower() in hay for x in pats)]
    # prefer a match in the author field
    a = [y for y in hits if any(x.lower() in p["author"].lower() for x in M["yeshivot"][y])]
    return (a or hits or [None])[0]

out = {}
for p in found.values():
    y = who(p)
    if y: out.setdefault(y, []).append(p)
for v in out.values(): v.sort(key=lambda p: -p["count"])
(ROOT / "data/podcasts_found.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
print("attributed", sum(len(v) for v in out.values()), "podcasts to", len(out), "yeshivot")
