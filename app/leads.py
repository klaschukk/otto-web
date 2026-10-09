"""POST /api/lead: заявка → SQLite + уведомление в Telegram."""
import json
import re
import threading
import urllib.parse
import urllib.request

from flask import Blueprint, current_app, jsonify, redirect, request

from . import LANGS, get_db

bp = Blueprint("leads", __name__)


def clean(value, limit):
    return re.sub(r"\s+", " ", (value or "")).strip()[:limit]


def notify_telegram(token, chat_id, text):
    if not token or not chat_id:
        return
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    try:
        urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", data, timeout=8)
    except Exception as e:  # заявка уже в БД, уведомление не критично
        print(f"telegram notify failed: {e}", flush=True)


@bp.post("/api/lead")
def lead():
    f = request.form
    lang = f.get("lang") if f.get("lang") in LANGS else "bg"
    wants_json = request.headers.get("Accept", "").startswith("application/json")
    thanks = ("" if lang == "bg" else f"/{lang}") + "/blagodarim/"

    def done(status=200, **payload):
        if wants_json:
            return jsonify(payload), status
        return redirect(thanks if status == 200 else request.referrer or "/", 303)

    # honeypot: люди это поле не видят, боты заполняют
    if f.get("website"):
        return done(ok=True)

    name, phone = clean(f.get("name"), 80), clean(f.get("phone"), 40)
    business = clean(f.get("business"), 120)
    message, source = clean(f.get("message"), 1000), clean(f.get("source"), 60)
    errors = {}
    if len(name) < 2:
        errors["name"] = "name"
    if len(re.sub(r"\D", "", phone)) < 6:
        errors["phone"] = "phone"
    if errors:
        return done(400, ok=False, errors=errors)

    db = get_db()
    # срок хранения из политики конфиденциальности: 12 месяцев
    db.execute("DELETE FROM leads WHERE ts < datetime('now','-12 months')")
    ip = request.remote_addr or ""
    recent = db.execute("SELECT COUNT(*) FROM leads WHERE ip=? AND ts > datetime('now','-1 hour')", (ip,)).fetchone()[0]
    if recent >= current_app.config["LEADS_PER_HOUR"]:
        return done(429, ok=False, errors={"form": "rate"})

    cur = db.execute("INSERT INTO leads(name,business,phone,message,source,lang,ip) VALUES(?,?,?,?,?,?,?)",
                     (name, business, phone, message, source, lang, ip))
    db.commit()

    text = f"Otto.web · нова заявка #{cur.lastrowid}\n{name} · {business or '—'}\n{phone}\n{message}\nот: {source or '—'} ({lang})"
    cfg = current_app.config
    if not cfg.get("TESTING"):
        threading.Thread(target=notify_telegram, args=(cfg["TELEGRAM_TOKEN"], cfg["TELEGRAM_CHAT_ID"], text),
                         daemon=True).start()
    return done(ok=True, id=cur.lastrowid)
