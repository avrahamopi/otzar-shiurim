"""Build dist/: index.html with app.js inlined, and data.js with the shiurim
(a separate file so the browser caches it and the page itself stays light)."""
import json, pathlib, datetime, hashlib
root = pathlib.Path(__file__).parent.parent
KEEP = {"t", "r", "c", "y", "v", "a", "d", "dt", "yr", "sr"}
data = {
    "yeshivot": json.loads((root / "data/yeshivot.json").read_text(encoding="utf-8")),
    "shiurim": [{k: v for k, v in x.items() if k in KEEP and v not in (None, "")}
                for x in json.loads((root / "data/shiurim.json").read_text(encoding="utf-8"))],
    "channels": json.loads((root / "data/channels.json").read_text(encoding="utf-8")),
    "feeds": json.loads((root / "dist/feeds/index.json").read_text(encoding="utf-8")) if (root / "dist/feeds/index.json").exists() else [],
    "updated": datetime.date.today().strftime("%d.%m.%Y"),
}
blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
app = (root / "app.js").read_text(encoding="utf-8")
html = (root / "index.html").read_text(encoding="utf-8")
(root / "dist").mkdir(exist_ok=True)
js = f"window.__DATA__={blob};"
(root / "dist/data.js").write_text(js, encoding="utf-8")
ver = hashlib.sha1(js.encode()).hexdigest()[:10]
html = html.replace("<script>/*APP*/</script>", f'<script src="data.js?v={ver}"></script>\n<script>{app}</script>')
(root / "dist/index.html").write_text(html, encoding="utf-8")
print("built", len(data["shiurim"]), "shiurim,", len(data["yeshivot"]), "yeshivot")
