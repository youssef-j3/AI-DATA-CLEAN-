import os
import sys
from markdown import markdown
from weasyprint import HTML

SRC = os.path.join(os.path.dirname(__file__), '..', 'docs', 'final_report.md')
OUT_HTML = os.path.join(os.path.dirname(__file__), '..', 'docs', 'final_report.html')
OUT_PDF = os.path.join(os.path.dirname(__file__), '..', 'docs', 'final_report.pdf')


def md_to_pdf(src_md=SRC, out_html=OUT_HTML, out_pdf=OUT_PDF):
    with open(src_md, 'r', encoding='utf-8') as f:
        md = f.read()
    # convert markdown to HTML
    html_body = markdown(md, output_format='html5')
    html = f"<html><head><meta charset='utf-8'><title>Final Report</title></head><body>{html_body}</body></html>"
    with open(out_html, 'w', encoding='utf-8') as f:
        f.write(html)
    # render PDF
    try:
        HTML(string=html, base_url=os.path.dirname(src_md)).write_pdf(out_pdf)
        print(f"Saved PDF to: {out_pdf}")
    except Exception as e:
        print('PDF conversion failed:', e)
        sys.exit(1)


if __name__ == '__main__':
    md_to_pdf()
