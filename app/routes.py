"""Публичные страницы. Язык по префиксу: / (bg), /en/, /ru/."""
from pathlib import Path

import yaml
from flask import (Blueprint, abort, current_app, render_template, request,
                   send_from_directory, url_for)

from . import LANGS, ROOT

bp = Blueprint("pages", __name__)
DEMO_DIR = ROOT / "site" / "demo"
PAGES = {  # endpoint -> путь без языкового префикса
    "home": "/", "raboti": "/raboti/", "ceni": "/ceni/", "kontakt": "/kontakt/",
}

with open(Path(__file__).parent / "works.yaml", encoding="utf-8") as f:
    WORKS = yaml.safe_load(f)


def prefix(lang):
    return "" if lang == "bg" else f"/{lang}"


def ctx(lang, page_path, **extra):
    """Общий контекст: тексты, студия, ссылки на эту же страницу на других языках."""
    t = current_app.config["T"][lang]
    alt = {l: prefix(l) + page_path for l in LANGS}
    works = [{**w, "niche": w["niche"][lang], "feature": w["feature"][lang],
              "idea": w["idea"][lang], "did": w["did"][lang]} for w in WORKS]
    return dict(t=t, lang=lang, P=prefix(lang), studio=current_app.config["STUDIO"],
                alt=alt, page_path=page_path, works=works, cfg=current_app.config, **extra)


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
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
           'xmlns:xhtml="http://www.w3.org/1999/xhtml">' + "".join(urls) + "</urlset>\n")
    return xml, 200, {"Content-Type": "application/xml"}


@bp.app_errorhandler(404)
def not_found(_e):
    lang = request.path.split("/")[1] if request.path.split("/")[1] in ("en", "ru") else "bg"
    return render_template("404.html", **ctx(lang, "/")), 404
