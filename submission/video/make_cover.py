"""Compose the 16:9 cover: Gemini background (build/cover/bg.png) plus the title set in the deck's fonts.

    uv run --no-project --with playwright python submission/video/make_cover.py
Output: submission/cover.png and submission/cover.jpg (1920x1080)
"""
import base64
from pathlib import Path

from playwright.sync_api import sync_playwright

SUB = Path(__file__).resolve().parent.parent
bg = "data:image/png;base64," + base64.b64encode((SUB / "video/build/cover/bg.png").read_bytes()).decode()
PAGE = f"""<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300..700&family=IBM+Plex+Mono:wght@400;600&display=swap">
<style>*{{margin:0;box-sizing:border-box}}
body{{width:1920px;height:1080px;overflow:hidden;font-family:'IBM Plex Sans',sans-serif;color:#F5F2EC;
  background:url({bg}) center/cover}}
.shade{{position:absolute;inset:0;background:linear-gradient(90deg,rgba(21,32,43,.94) 0%,rgba(21,32,43,.78) 38%,rgba(21,32,43,0) 62%)}}
.text{{position:absolute;left:128px;top:0;bottom:0;width:900px;display:flex;flex-direction:column;justify-content:center;gap:32px}}
.eyebrow{{font-family:'IBM Plex Mono',monospace;font-size:28px;letter-spacing:2px;color:#E2622B}}
h1{{font-size:112px;font-weight:600;line-height:1.02}}
.sub{{font-size:40px;font-weight:300;line-height:1.3;color:#BFCAD4}}
.foot{{font-family:'IBM Plex Mono',monospace;font-size:26px;color:#BFCAD4}}</style></head>
<body><div class="shade"></div><div class="text">
<p class="eyebrow">AMD DEVELOPER HACKATHON: ACT III</p>
<h1>Compressor<br>Maintenance<br>Copilot</h1>
<p class="sub">Catch the air leak before the line stops.</p>
<p class="foot">Evolus agent · open model on AMD GPUs · team gheware</p>
</div></body></html>"""

with sync_playwright() as p:
    page = p.chromium.launch().new_page(viewport={"width": 1920, "height": 1080})
    page.set_content(PAGE, wait_until="networkidle")
    page.evaluate("""Promise.all(['600 112px "IBM Plex Sans"', '300 40px "IBM Plex Sans"', '400 28px "IBM Plex Mono"']
                     .map(f => document.fonts.load(f))).then(() => document.fonts.ready)""")
    page.wait_for_timeout(300)
    page.screenshot(path=str(SUB / "cover.png"))
    page.screenshot(path=str(SUB / "cover.jpg"), type="jpeg", quality=90)
print("wrote", SUB / "cover.png", "and cover.jpg")
