"""Turn data/raw.tsv (collected by hand from YouTube) into data/shiurim.json."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from tagger import tag, to_minutes

root = pathlib.Path(__file__).parent.parent / "data"
out = []
for line in (root / "raw.tsv").read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    y, vid, title, dur, date = line.split("\t")
    s = tag(title)
    s.update({"y": y, "v": vid, "d": to_minutes(dur), "dt": date})
    out.append(s)
for line in (root / "raw_audio.tsv").read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    cols = line.split("\t") + ["", "", ""]
    y, a, vid, title, date, rabbi, yr, dur = cols[:8]
    s = tag(title)
    if rabbi:
        s["r"] = rabbi
    s.update({"y": y, "v": vid or None, "a": a, "d": int(dur) if dur else None, "dt": date})
    if yr:
        s["yr"] = yr
    out.append(s)
(root / "shiurim.json").write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")
print(len(out), "shiurim")
for s in out:
    print(f'{s["y"]:11} {s["c"]:14} {s["r"]:22} {s["t"][:60]}')
