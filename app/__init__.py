"""Otto.web: сайт студии. Flask + SQLite, тексты в app/i18n/*.yaml."""
import os
import re
import sqlite3
from pathlib import Path

import yaml
from markupsafe import Markup
from flask import Flask, g
from werkzeug.middleware.proxy_fix import ProxyFix

ROOT = Path(__file__).resolve().parent.parent
LANGS = ("bg", "en", "ru")


def load_env(path):
    """Простой .env без зависимостей: KEY=VALUE, переменные окружения важнее."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))


def create_app(test_config=None):
    load_env(ROOT / ".env")
    app = Flask(__name__, static_folder=str(ROOT / "static"), static_url_path="/static")
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        DB_PATH=os.environ.get("DB_PATH", str(ROOT / "data" / "otto.db")),
        ADMIN_USER=os.environ.get("ADMIN_USER", "kirill"),
        ADMIN_PASSWORD=os.environ.get("ADMIN_PASSWORD", ""),
        TELEGRAM_TOKEN=os.environ.get("TELEGRAM_TOKEN", ""),
        TELEGRAM_CHAT_ID=os.environ.get("TELEGRAM_CHAT_ID", ""),
        BASE_URL=os.environ.get("BASE_URL", "https://otto-web.online").rstrip("/"),
        GIT_SHA=os.environ.get("GIT_SHA", "dev"),
        UMAMI_SRC=os.environ.get("UMAMI_SRC", ""),
        UMAMI_ID=os.environ.get("UMAMI_ID", ""),
        GOOGLE_SITE_VERIFICATION=os.environ.get("GOOGLE_SITE_VERIFICATION", ""),
        LEADS_PER_HOUR=5,
        SEND_FILE_MAX_AGE_DEFAULT=60 * 60 * 24 * 7,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("BASE_URL", "").startswith("https://"),
    )
    if test_config:
        app.config.update(test_config)

    # nginx перед приложением: берём IP клиента из X-Forwarded-For (один прокси)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    with open(ROOT / "site.yaml", encoding="utf-8") as f:
        app.config["STUDIO"] = yaml.safe_load(f)
    app.config["T"] = {}
    for lang in LANGS:
        with open(ROOT / "app" / "i18n" / f"{lang}.yaml", encoding="utf-8") as f:
            app.config["T"][lang] = yaml.safe_load(f)

    Path(app.config["DB_PATH"]).parent.mkdir(parents=True, exist_ok=True)
    init_db(app.config["DB_PATH"])
    app.teardown_appcontext(close_db)

    def asset_v(name):
        """Версия файла для ?v=: меняется при каждом изменении, кеш на 7 дней не мешает."""
        try:
            return int((ROOT / "static" / name).stat().st_mtime)
        except OSError:
            return app.config["GIT_SHA"]
    app.jinja_env.globals["asset_v"] = asset_v

    css_cache = {}

    def inline_css(name):
        """CSS в <head> вместо <link>: страницы открывают по ссылке один раз, лишний запрос до отрисовки дороже кеша."""
        path = ROOT / "static" / name
        key = (name, path.stat().st_mtime)
        if key not in css_cache:
            css_cache[key] = Markup(path.read_text(encoding="utf-8").replace("</", "<\\/"))
        return css_cache[key]
    app.jinja_env.globals["inline_css"] = inline_css

    def nb(text):
        """Короткие предлоги и союзы не остаются в конце строки заголовка: «в Бургас» переносится целиком."""
        out = re.sub(r"(?<=\s)(в|във|за|и|с|със|на|от|до|по|для|без|a|in|for|to|of)\s", lambda m: m.group(1) + "\u00a0", str(text), flags=re.I)
        return Markup(out) if isinstance(text, Markup) else out
    app.jinja_env.filters["nb"] = nb

    from . import admin, ledger, leads, routes
    app.register_blueprint(routes.bp)
    app.register_blueprint(leads.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(ledger.bp)
    return app


SCHEMA = """
CREATE TABLE IF NOT EXISTS leads(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL DEFAULT (datetime('now')),
  name TEXT NOT NULL,
  business TEXT NOT NULL DEFAULT '',
  phone TEXT NOT NULL,
  message TEXT NOT NULL DEFAULT '',
  source TEXT NOT NULL DEFAULT '',
  lang TEXT NOT NULL DEFAULT 'bg',
  ip TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'new'
);
CREATE INDEX IF NOT EXISTS leads_ip_ts ON leads(ip, ts);
CREATE TABLE IF NOT EXISTS deals(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL DEFAULT (date('now')),
  venue TEXT NOT NULL,
  phone TEXT NOT NULL DEFAULT '',
  channel TEXT NOT NULL DEFAULT '',
  stage TEXT NOT NULL DEFAULT 'contact',
  package TEXT NOT NULL DEFAULT '',
  price REAL NOT NULL DEFAULT 0,
  next_step TEXT NOT NULL DEFAULT '',
  next_date TEXT NOT NULL DEFAULT '',
  updated TEXT NOT NULL DEFAULT (date('now'))
);
CREATE TABLE IF NOT EXISTS money(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  day TEXT NOT NULL DEFAULT (date('now')),
  kind TEXT NOT NULL CHECK (kind IN ('in','out')),
  amount REAL NOT NULL,
  category TEXT NOT NULL DEFAULT '',
  deal_id INTEGER,
  note TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS hours(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  day TEXT NOT NULL DEFAULT (date('now')),
  deal_id INTEGER,
  hours REAL NOT NULL,
  what TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS activity(
  day TEXT PRIMARY KEY,
  contacts INTEGER NOT NULL DEFAULT 0,
  replies INTEGER NOT NULL DEFAULT 0,
  shows INTEGER NOT NULL DEFAULT 0
);
"""


def init_db(path):
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    con.close()


def get_db():
    from flask import current_app
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DB_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
