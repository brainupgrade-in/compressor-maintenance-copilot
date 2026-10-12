"""Render the deck's slide files to 1920x1080 PNGs for the video (approximation of the Slides runtime).

    uv run --no-project --with playwright python submission/video/render_slides.py
"""
import base64
import json
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

SUB = Path(__file__).resolve().parent.parent
DECK = SUB / "deck/project"
OUT = SUB / "video/build/slides"
# set_content pages cannot load file:// images, so the screenshots go in as data URIs (render only)
data_uri = lambda f: "data:image/jpeg;base64," + base64.b64encode((SUB / "assets" / f).read_bytes()).decode()
BLOBS = {"/_blob/1351031cb1aa5dde0612bdb45761b1d9": data_uri("app-detector.jpg"),
         "/_blob/37bf21aacd3a112f5526142924a37b5f": data_uri("app-agent.jpg")}
ARROW = ('<svg width="48" height="24" viewBox="0 0 48 24" style="flex:none"><path d="M0 7h29V0l19 12-19 12v-7H0z" '
         'fill="{c}"/></svg>')
PAGE = """<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300..700&family=IBM+Plex+Mono:wght@400;600&display=swap">
<style>*{{margin:0;box-sizing:border-box}} body{{width:1920px;height:1080px;overflow:hidden}}
section{{position:relative;width:1920px;height:1080px}} aside{{display:none}} ul{{padding-left:1.2em}}
table{{border-collapse:collapse;width:100%}} th,td{{padding:0.35em 0.6em;border-bottom:1px solid #DDD6C9}}</style>
</head><body>{body}</body></html>"""


def html(slide: str) -> str:
    for blob, uri in BLOBS.items():
        slide = slide.replace(blob, uri)
    return re.sub(r'<x-shape kind="arrow-right" style="background:(#[0-9A-Fa-f]+)[^"]*"></x-shape>',
                  lambda m: ARROW.format(c=m.group(1)), slide)


OUT.mkdir(parents=True, exist_ok=True)
order = json.loads((DECK / "deck.json").read_text())["order"]
with sync_playwright() as p:
    page = p.chromium.launch().new_page(viewport={"width": 1920, "height": 1080})
    for i, sid in enumerate(order, 1):
        page.set_content(PAGE.format(body=html((DECK / f"slides/{sid}.html").read_text())), wait_until="networkidle")
        page.evaluate("""Promise.all(['400 30px "IBM Plex Mono"', '600 72px "IBM Plex Mono"', '600 64px "IBM Plex Sans"']
                         .map(f => document.fonts.load(f))).then(() => document.fonts.ready)""")
        page.wait_for_timeout(300)
        page.screenshot(path=str(OUT / f"{i:02d}-{sid}.png"))
        print("rendered", sid)
