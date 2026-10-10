"""Печатные материалы: HTML из этой папки -> PDF в print/out/ (папка не коммитится).

    .venv/bin/python print/render.py            # все *.html
    .venv/bin/python print/render.py listovka   # один файл
"""
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"


def main():
    chrome = shutil.which("chromium") or shutil.which("google-chrome")
    if not chrome:
        sys.exit("Нужен chromium.")
    names = sys.argv[1:] or [p.stem for p in sorted(HERE.glob("*.html"))]
    OUT.mkdir(exist_ok=True)
    for name in names:
        src, pdf = HERE / f"{name}.html", OUT / f"{name}.pdf"
        subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                        "--virtual-time-budget=5000", f"--print-to-pdf={pdf}", src.as_uri()],
                       check=True, capture_output=True, timeout=120)
        print(pdf)


if __name__ == "__main__":
    main()
