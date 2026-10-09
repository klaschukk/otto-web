"""Договор: шаблон dogovor.html + реквизиты из firm.local.yaml -> out/dogovor.html и out/dogovor.pdf.

firm.local.yaml в .gitignore (репо публичный: адрес и IBAN туда не попадают).
Образец полей: firm.example.yaml.

    .venv/bin/python contract/render.py            # HTML + PDF
    .venv/bin/python contract/render.py --no-pdf   # только HTML
"""
import shutil
import subprocess
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"


def main():
    local = HERE / "firm.local.yaml"
    if not local.exists():
        sys.exit("Нет contract/firm.local.yaml: скопируйте firm.example.yaml и впишите реквизиты.")
    firm = yaml.safe_load(local.read_text(encoding="utf-8"))
    env = Environment(loader=FileSystemLoader(HERE), undefined=StrictUndefined, autoescape=True)
    html = env.get_template("dogovor.html").render(firm=firm)

    OUT.mkdir(exist_ok=True)
    out_html = OUT / "dogovor.html"
    out_html.write_text(html, encoding="utf-8")
    print(out_html)

    if "--no-pdf" in sys.argv:
        return
    chrome = shutil.which("chromium") or shutil.which("google-chrome")
    if not chrome:
        sys.exit("Нет chromium: PDF не собран, HTML готов.")
    out_pdf = OUT / "dogovor.pdf"
    subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=5000", f"--print-to-pdf={out_pdf}", out_html.as_uri()],
                   check=True, capture_output=True, timeout=120)
    print(out_pdf)


if __name__ == "__main__":
    main()
