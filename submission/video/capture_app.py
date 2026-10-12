"""Capture the live demo app for the video (1920x1080 PNGs). The chat questions are live AMD calls.

    uv run --no-project --with playwright python submission/video/capture_app.py
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "https://agenticai-compressor.brainupgrade.in"
OUT = Path(__file__).resolve().parent / "build/app"
OUT.mkdir(parents=True, exist_ok=True)


def shot(page, name, el=None):
    if el is not None:  # put the element near the top of the frame
        el.evaluate("e => e.scrollIntoView({block: 'start'})")
        page.mouse.wheel(0, -120)
        page.wait_for_timeout(800)
    page.screenshot(path=str(OUT / f"{name}.png"))
    print("captured", name)


def ask(page, question, n_answers):
    box = page.locator('textarea[data-testid="stChatInputTextArea"]')
    box.fill(question)
    box.press("Enter")
    page.locator('[data-testid="stChatMessage"]').nth(2 * n_answers - 1).wait_for(timeout=240_000)
    page.wait_for_timeout(1500)
    return page.locator('[data-testid="stChatMessage"]').nth(2 * n_answers - 2)


with sync_playwright() as p:
    page = p.chromium.launch().new_page(viewport={"width": 1920, "height": 1080}, color_scheme="dark")
    page.goto(URL, timeout=120_000)
    page.get_by_text("Recorded failures warned before onset").wait_for(timeout=180_000)
    page.wait_for_timeout(3000)
    shot(page, "a01-overview")
    shot(page, "a02-chart", page.get_by_text("Alert", exact=True).first)

    page.get_by_role("button", name="Explain with the AMD-hosted agent").click()
    page.get_by_text("What is happening.").wait_for(timeout=240_000)
    page.wait_for_timeout(1500)
    shot(page, "a03-explain", page.get_by_text("Saved answer from a live run"))
    shot(page, "a04-workorder", page.get_by_text("Checks to do"))

    shot(page, "a05-chat", ask(page, "What did we do last time this happened?", 1))
    shot(page, "a06-safety", ask(page, "Can I keep running it until the weekend?", 2))

    page.mouse.wheel(0, -40000)
    page.get_by_role("tab", name="Ask the Evolus agent").click()
    frame = page.frame_locator("iframe").first
    frame.get_by_text("How do I confirm an air leak?").first.click(timeout=60_000)
    page.wait_for_timeout(45_000)  # live answer through the Evolus widget
    shot(page, "a07-widget")

    page.get_by_role("tab", name="Milling machine (AI4I 2020)").click()
    page.wait_for_timeout(5000)
    shot(page, "a08-ai4i")
