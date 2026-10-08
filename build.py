#!/usr/bin/env python3
"""Сборка сайта Otto.web: витрина + демо-сайты для бизнесов.

  site.yaml            настройки студии (телефон, цены, домен)
  demos/<slug>.yaml    один демо-сайт; ключ niche выбирает шаблон templates/<niche>.html.j2
  site/                результат, его публикует GitHub Pages

python build.py           собрать всё
python build.py --serve   собрать и открыть на http://127.0.0.1:8000
"""
import shutil
import sys
from pathlib import Path

import segno
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).parent
OUT = ROOT / "site"


def load(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    studio = load(ROOT / "site.yaml")
    base_url = studio.get("base_url", "").rstrip("/")
    env = Environment(loader=FileSystemLoader(ROOT / "templates"),
                      autoescape=select_autoescape(["html", "j2"]))

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "static", OUT / "static")

    demos = []
    for path in sorted((ROOT / "demos").glob("*.yaml")):
        d = load(path)
        d["slug"] = path.stem
        d.setdefault("is_demo", True)
        out = OUT / "demo" / d["slug"]
        out.mkdir(parents=True)
        if d.get("qr"):
            # QR ведёт на живую страницу демо — владелец сканирует своим телефоном
            segno.make(f"{base_url}/demo/{d['slug']}/", error="m").save(
                out / "qr.svg", scale=6, border=2, dark="#111")
        html = env.get_template(f"{d['niche']}.html.j2").render(d=d, studio=studio)
        (out / "index.html").write_text(html, encoding="utf-8")
        demos.append(d)
        print(f"  demo/{d['slug']}/  ({d['niche']})")

    showcase = [d for d in demos if d.get("showcase")]
    ctx = dict(studio=studio, demos=showcase)
    (OUT / "index.html").write_text(env.get_template("storefront.html.j2").render(**ctx), encoding="utf-8")
    (OUT / "demo" / "index.html").write_text(env.get_template("gallery.html.j2").render(**ctx), encoding="utf-8")
    (OUT / "404.html").write_text(env.get_template("404.html.j2").render(**ctx), encoding="utf-8")

    # демо не индексируем: там вымышленные бизнесы или чужие названия
    (OUT / "robots.txt").write_text(
        f"User-agent: *\nDisallow: /demo/\nSitemap: {base_url}/sitemap.xml\n", encoding="utf-8")
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<url><loc>{base_url}/</loc></url></urlset>\n", encoding="utf-8")
    if studio.get("domain"):
        (OUT / "CNAME").write_text(studio["domain"] + "\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"✓ site/ собран: витрина + {len(demos)} демо")

    if "--serve" in sys.argv:
        import functools, http.server
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
        print("→ http://127.0.0.1:8000")
        http.server.ThreadingHTTPServer(("127.0.0.1", 8000), handler).serve_forever()


if __name__ == "__main__":
    main()
