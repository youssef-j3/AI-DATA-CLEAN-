import asyncio
import os
from pyppeteer import launch

SRC_HTML = os.path.join(os.path.dirname(__file__), '..', 'docs', 'exec_summary.html')
OUT_PDF = os.path.join(os.path.dirname(__file__), '..', 'docs', 'exec_summary.pdf')

async def html_to_pdf(src_html, out_pdf):
    url = 'file://' + os.path.abspath(src_html)
    possible_execs = [
        r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        r"C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
        r"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    ]
    exe_path = None
    for p in possible_execs:
        if os.path.exists(p):
            exe_path = p
            break
    if exe_path:
        browser = await launch(executablePath=exe_path, args=['--no-sandbox'])
    else:
        browser = await launch(args=['--no-sandbox'])
    page = await browser.newPage()
    await page.goto(url)
    await asyncio.sleep(0.5)
    await page.pdf({'path': out_pdf, 'format': 'A4', 'printBackground': True})
    await browser.close()
    print(f"Saved PDF to: {out_pdf}")

if __name__ == '__main__':
    asyncio.run(html_to_pdf(SRC_HTML, OUT_PDF))
