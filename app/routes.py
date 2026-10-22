"""Публичные страницы. Язык по префиксу: / (bg), /en/, /ru/."""
from pathlib import Path

import yaml
from flask import (Blueprint, abort, current_app, render_template, request,
                   send_from_directory, url_for)

from . import LANGS, ROOT

bp = Blueprint("pages", __name__)
DEMO_DIR = ROOT / "site" / "demo"
PAGES = {  # endpoint -> путь без языкового префикса
    "home": "/", "raboti": "/raboti/", "ceni": "/ceni/", "kontakt": "/kontakt/", "poveritelnost": "/poveritelnost/",
}

with open(Path(__file__).parent / "works.yaml", encoding="utf-8") as f:
    WORKS = yaml.safe_load(f)
with open(Path(__file__).parent / "articles.yaml", encoding="utf-8") as f:
    ARTICLES = yaml.safe_load(f)  # «Полезно»: статьи только на болгарском
with open(Path(__file__).parent / "landings.yaml", encoding="utf-8") as f:
    LANDINGS = yaml.safe_load(f)  # посадочные под поисковые запросы, по одной на нишу


def prefix(lang):
    return "" if lang == "bg" else f"/{lang}"


def ctx(lang, page_path, **extra):
    """Общий контекст: тексты, студия, ссылки на эту же страницу на других языках."""
    t = current_app.config["T"][lang]
    alt = {l: prefix(l) + page_path for l in LANGS}
    works = [{**w, "niche": w["niche"][lang], "feature": w["feature"][lang],
              "idea": w["idea"][lang], "did": w["did"][lang]} for w in WORKS]
    pages = [{"slug": p["slug"], "work": p["work"], "name": p["name"][lang], "h1": p[lang]["h1"], "town": p.get("kind") == "town"}
             for p in LANDINGS["pages"]]
    landings = [p for p in pages if not p["town"]]  # ниши
    towns = [p for p in pages if p["town"]]  # города около Бургаса
    return dict(t=t, lang=lang, P=prefix(lang), studio=current_app.config["STUDIO"], alt=alt, page_path=page_path,
                works=works, landings=landings, towns=towns, ll=LANDINGS["labels"][lang], cfg=current_app.config, **extra)


def page(endpoint_name, path):
    """Регистрирует одну страницу на трёх языках."""
    def deco(fn):
        for lang in LANGS:
            def view(fn=fn, lang=lang, **kw):
                return fn(lang, **kw)
            bp.add_url_rule(prefix(lang) + path, f"{endpoint_name}_{lang}", view)
        return fn
    return deco


@page("home", "/")
def home(lang):
    return render_template("home.html", **ctx(lang, "/"))


@page("raboti", "/raboti/")
def raboti(lang):
    return render_template("raboti.html", **ctx(lang, "/raboti/"))


@page("rabota", "/raboti/<slug>/")
def rabota(lang, slug):
    c = ctx(lang, f"/raboti/{slug}/")
    work = next((w for w in c["works"] if w["slug"] == slug), None)
    if not work:
        abort(404)
    i = c["works"].index(work)
    return render_template("rabota.html", work=work, nxt=c["works"][(i + 1) % len(c["works"])], **c)


@page("ceni", "/ceni/")
def ceni(lang):
    return render_template("ceni.html", **ctx(lang, "/ceni/"))


@page("kontakt", "/kontakt/")
def kontakt(lang):
    return render_template("kontakt.html", **ctx(lang, "/kontakt/"))


@page("blagodarim", "/blagodarim/")
def blagodarim(lang):
    return render_template("blagodarim.html", **ctx(lang, "/blagodarim/"))


@page("poveritelnost", "/poveritelnost/")
def poveritelnost(lang):
    return render_template("poveritelnost.html", **ctx(lang, "/poveritelnost/"))


def landing(p):
    """Посадочная страница ниши: /<slug>/ на трёх языках, тексты из landings.yaml."""
    path = f"/{p['slug']}/"

    @page(p["slug"], path)
    def view(lang):
        c = ctx(lang, path)
        work = next(w for w in c["works"] if w["slug"] == p["work"])
        area = p["name"]["en"] if p.get("kind") == "town" else "Burgas"
        return render_template("usluga.html", pg=p[lang], slug=p["slug"], work=work, area=area, **c)

    PAGES[p["slug"]] = path  # попадает в sitemap


for _p in LANDINGS["pages"]:
    landing(_p)


@bp.route("/polezno/")
def polezno():
    c = ctx("bg", "/polezno/")
    c["alt"] = {"bg": "/polezno/"}
    return render_template("polezno.html", articles=ARTICLES, **c)


@bp.route("/polezno/<slug>/")
def article(slug):
    a = next((x for x in ARTICLES if x["slug"] == slug), None)
    if not a:
        abort(404)
    c = ctx("bg", f"/polezno/{slug}/")
    c["alt"] = {"bg": f"/polezno/{slug}/"}
    return render_template("article.html", a=a, others=[x for x in ARTICLES if x is not a], **c)


@bp.route("/demo/")
def demo_index():
    return send_from_directory(DEMO_DIR, "index.html")


@bp.route("/demo/<path:path>")
def demo(path):
    # демо собираются build.py в site/demo/ (ручные из custom/ + шаблонные из demos/)
    if path.endswith("/") or "." not in path.rsplit("/", 1)[-1]:
        path = path.rstrip("/") + "/index.html"
    resp = send_from_directory(DEMO_DIR, path)
    resp.headers["X-Robots-Tag"] = "noindex"
    return resp


@bp.route("/health")
def health():
    return f"ok {current_app.config['GIT_SHA']}\n", 200, {"Content-Type": "text/plain"}


@bp.route("/favicon.ico")
def favicon():
    # браузеры и поисковики просят этот адрес сами, в том числе на демо-страницах без <link rel="icon">
    return current_app.send_static_file("favicon.ico")


@bp.route("/robots.txt")
def robots():
    base = current_app.config["BASE_URL"]
    body = f"User-agent: *\nDisallow: /demo/\nDisallow: /admin/\nSitemap: {base}/sitemap.xml\n"
    return body, 200, {"Content-Type": "text/plain"}


@bp.route("/sitemap.xml")
def sitemap():
    base = current_app.config["BASE_URL"]
    paths = list(PAGES.values()) + [f"/raboti/{w['slug']}/" for w in WORKS]
    urls = []
    for p in paths:
        links = "".join(f'<xhtml:link rel="alternate" hreflang="{l}" href="{base}{prefix(l)}{p}"/>' for l in LANGS)
        for l in LANGS:
            urls.append(f"<url><loc>{base}{prefix(l)}{p}</loc>{links}</url>")
    for p in ["/polezno/"] + [f"/polezno/{a['slug']}/" for a in ARTICLES]:
        urls.append(f'<url><loc>{base}{p}</loc><xhtml:link rel="alternate" hreflang="bg" href="{base}{p}"/></url>')
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
           'xmlns:xhtml="http://www.w3.org/1999/xhtml">' + "".join(urls) + "</urlset>\n")
    return xml, 200, {"Content-Type": "application/xml"}


@bp.app_errorhandler(404)
def not_found(_e):
    lang = request.path.split("/")[1] if request.path.split("/")[1] in ("en", "ru") else "bg"
    return render_template("404.html", **ctx(lang, "/")), 404
