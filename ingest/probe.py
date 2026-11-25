"""Probe WordPress post types found by discover.py: does a type carry audio files?
Writes data/wp_probe.json: {yeshiva: [{site, type, rest_base, total, with_audio_in_first_page, sample}]}"""
import json, re, urllib.request, urllib.parse
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
STD = {'post','page','attachment','nav_menu_item','wp_block','wp_template','wp_template_part','wp_global_styles',
       'wp_navigation','wp_font_family','wp_font_face','elementor_library','e-floating-buttons','elementor_snippet',
       'mailpoet_email','product','jp_act_log_event','jet-engine','jet-popup','oceanwp_library','ditty','ditty_layout',
       'ditty_display','woolentor-template','elementskit_content','envira','news-ticker'}
AUD = re.compile(r'https?:[^"\'\s<>]+?\.(?:mp3|m4a)', re.I)
def get(u):
    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.headers, r.read(4_000_000).decode("utf-8", "replace")
d = json.loads((ROOT / "data/discovery.json").read_text())
out = {}
for yid, v in d.items():
    for s in v["sites"]:
        types = s.get("wp_types") or {}
        base = s.get("final", s["url"])
        root = urllib.parse.urlsplit(base)._replace(path="", query="", fragment="").geturl()
        for t, rb in types.items():
            if t in STD or not rb: continue
            u = f"{root}/wp-json/wp/v2/{rb}?per_page=20&_embed=0"
            try:
                h, body = get(u)
                items = json.loads(body)
                aud = [m for m in AUD.findall(body.replace('\\/', '/'))]
                out.setdefault(yid, []).append({"site": root, "type": t, "rest_base": rb,
                    "total": h.get("X-WP-Total"), "audio_hits": len(aud), "sample": aud[:3],
                    "keys": sorted(items[0].keys())[:40] if items else []})
            except Exception as e:
                out.setdefault(yid, []).append({"site": root, "type": t, "rest_base": rb, "error": str(e)[:100]})
            print(yid, t, flush=True)
(ROOT / "data/wp_probe.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
