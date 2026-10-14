"""Картинки превью ссылок (Open Graph, 1200×630): главная на трёх языках и пять посадочных.
Тексты берутся из app/i18n/*.yaml и app/landings.yaml. Запуск: make og (HTML → PNG через headless Chromium)."""
import html, json, os, re, subprocess, sys
from pathlib import Path
import yaml

R = Path(__file__).resolve().parent.parent
OUT = R / "static" / "og"
TMP = R / "social" / "og_build"
FONTS = R / "static" / "fonts"
LANGS = ("bg", "ru", "en")
LINE = {  # нижняя строка: город и ниши, на главной
    "bg": "Бургас · ресторанти, салони, сервизи",
    "ru": "Бургас · рестораны, салоны, автосервисы",
    "en": "Burgas · restaurants, salons, garages",
}
FREE = {"bg": "първо безплатен пример", "ru": "сначала бесплатный пример", "en": "a free sample first"}


def css():
    faces = []
    for w in (500, 800):
        for f in sorted(FONTS.glob("onest-*.woff2")):
            faces.append(f'@font-face{{font-family:Onest;font-weight:{w};src:url("file://{f}")}}')
    for f in sorted(FONTS.glob("ibm-plex-mono-*.woff2")):
        faces.append(f'@font-face{{font-family:Plex;font-weight:500;src:url("file://{f}")}}')
    return "".join(faces) + """
*{margin:0;box-sizing:border-box}
body{width:1200px;height:630px;background:#0e0f11;color:#fff;font-family:Onest,sans-serif;padding:72px 84px;display:flex;flex-direction:column;justify-content:space-between}
.logo{font:800 44px/1 Onest;letter-spacing:-1.6px}.logo span{font:500 30px Plex;background:#ffe24a;color:#111214;padding:2px 8px;margin-left:4px;vertical-align:5px;letter-spacing:0}
h1{font:800 104px/1.02 Onest;letter-spacing:-4.5px;max-width:1040px}
h1.long{font-size:88px;letter-spacing:-3.6px}
h1 mark{background:#ffe24a;color:#111214;padding:0 12px}
.row{display:flex;align-items:center;gap:22px;font:500 30px Plex;color:#a3a7ad}
.row b{font-weight:500;background:#ffe24a;color:#111214;padding:4px 12px}
.row i{font-style:normal;color:#fff}
"""


def nbsp(s):
    """Короткие предлоги и союзы не висят в конце строки: «в Бургас» переносится целиком."""
    return re.sub(r"(?<=\s)(в|за|и|с|на|для|in|for)\s", lambda m: m.group(1) + "&nbsp;", s, flags=re.I)


def page(h1, row, long=False):
    h1 = nbsp(h1)
    return (f'<!doctype html><meta charset="utf-8"><style>{css()}</style>'
            f'<div class="logo">Otto<span>.web</span></div>'
            f'<h1 class="{"long" if long else ""}">{h1}</h1><div class="row">{row}</div>')


def main():
    TMP.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)
    land = yaml.safe_load(open(R / "app" / "landings.yaml", encoding="utf-8"))
    jobs = []
    for lang in LANGS:
        t = yaml.safe_load(open(R / "app" / "i18n" / f"{lang}.yaml", encoding="utf-8"))["hero"]
        h1 = f'{html.escape(t["h1_pre"])} <mark>{html.escape(t["h1_mark"])}</mark>{html.escape(t["h1_post"])}'
        row = f'<span>{html.escape(LINE[lang])}</span><b>{html.escape(t["price_from"])}</b>'
        jobs.append((f"og-{lang}", page(h1, row, long=len(t["h1_pre"]) > 20)))
        for p in land["pages"]:
            ll = land["labels"][lang]
            row = f'<i>otto-web.online</i><span>· {html.escape(FREE[lang])}</span><b>{html.escape(ll["from"])}</b>'
            jobs.append((f'og-{p["slug"]}-{lang}', page(html.escape(p[lang]["h1"]), row, long=len(p[lang]["h1"]) > 24)))
    for name, doc in jobs:
        (TMP / f"{name}.html").write_text(doc, encoding="utf-8")
    (TMP / "jobs.json").write_text(json.dumps([n for n, _ in jobs]), encoding="utf-8")
    # NODE_PATH с playwright-core задаётся в local.mk (не в репозитории), make og передаёт его сюда
    subprocess.run(["node", str(R / "social" / "render_og.js")], check=True, env=dict(os.environ))
    print(f"  static/og/: {len(jobs)} картинок")


if __name__ == "__main__":
    sys.exit(main())
