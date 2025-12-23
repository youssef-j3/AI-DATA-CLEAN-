import os
from markdown import markdown

SRC = os.path.join(os.path.dirname(__file__), '..', 'docs', 'change_log.md')
OUT_HTML = os.path.join(os.path.dirname(__file__), '..', 'docs', 'change_log.html')


def md_to_html(src_md=SRC, out_html=OUT_HTML):
    with open(src_md, 'r', encoding='utf-8') as f:
        md = f.read()
    css_path = os.path.join(os.path.dirname(src_md), 'print.css')
    css_link = ''
    if os.path.exists(css_path):
        css_link = "<link rel='stylesheet' href='print.css'>"
    html_body = markdown(md, output_format='html5')
    html = f"<html><head><meta charset='utf-8'><title>Change Log</title>{css_link}</head><body>{html_body}</body></html>"
    with open(out_html, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Saved HTML to: {out_html}")


if __name__ == '__main__':
    md_to_html()
