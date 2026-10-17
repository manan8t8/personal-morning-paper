import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

html_path, pdf_path = sys.argv[1], sys.argv[2]

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(Path(html_path).resolve().as_uri())
    page.pdf(path=pdf_path, format="A4", print_background=True)
    browser.close()