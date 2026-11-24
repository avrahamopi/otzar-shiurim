"""Bake data/*.json and app.js into one self-contained dist/index.html."""
import json, pathlib, datetime
root = pathlib.Path(__file__).parent.parent
data = {
    "yeshivot": json.loads((root / "data/yeshivot.json").read_text(encoding="utf-8")),
    "shiurim": json.loads((root / "data/shiurim.json").read_text(encoding="utf-8")),
    "channels": json.loads((root / "data/channels.json").read_text(encoding="utf-8")),
    "feeds": json.loads((root / "dist/feeds/index.json").read_text(encoding="utf-8")) if (root / "dist/feeds/index.json").exists() else [],
    "updated": datetime.date.today().strftime("%d.%m.%Y"),
}
blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
app = (root / "app.js").read_text(encoding="utf-8")
html = (root / "index.html").read_text(encoding="utf-8")
html = html.replace("<script>/*APP*/</script>", f"<script>window.__DATA__={blob};</script>\n<script>{app}</script>")
(root / "dist").mkdir(exist_ok=True)
(root / "dist/index.html").write_text(html, encoding="utf-8")
print("built", len(data["shiurim"]), "shiurim,", len(data["yeshivot"]), "yeshivot")
