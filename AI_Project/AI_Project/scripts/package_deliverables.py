import os
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'docs', 'deliverables.zip')
INCLUDE = [
    os.path.join(ROOT, 'docs', 'final_report.pdf'),
    os.path.join(ROOT, 'docs', 'final_report.html'),
    os.path.join(ROOT, 'docs', 'final_report_pyppeteer.pdf'),
    os.path.join(ROOT, 'docs', 'exec_summary.pdf'),
    os.path.join(ROOT, 'slides', 'final_deck.pptx'),
]
# include results folder files
results_dir = os.path.join(ROOT, 'results')
for root, dirs, files in os.walk(results_dir):
    for f in files:
        INCLUDE.append(os.path.join(root, f))

with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    for path in INCLUDE:
        if os.path.exists(path):
            arcname = os.path.relpath(path, ROOT)
            z.write(path, arcname)
print(f"Wrote deliverables ZIP: {OUT}")
