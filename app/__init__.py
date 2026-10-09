"""Otto.web: сайт студии. Flask + SQLite, тексты в app/i18n/*.yaml."""
import os
import sqlite3
from pathlib import Path

import yaml
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
        BASE_URL=os.environ.get("BASE_URL", "http://159.195.196.170:8080").rstrip("/"),
        GIT_SHA=os.environ.get("GIT_SHA", "dev"),
        UMAMI_SRC=os.environ.get("UMAMI_SRC", ""),
        UMAMI_ID=os.environ.get("UMAMI_ID", ""),
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

    from . import admin, leads, routes
    app.register_blueprint(routes.bp)
    app.register_blueprint(leads.bp)
    app.register_blueprint(admin.bp)
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
