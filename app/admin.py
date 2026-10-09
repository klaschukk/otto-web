"""/admin/: заявки из формы. Логин и пароль из .env (ADMIN_USER, ADMIN_PASSWORD)."""
import csv
import hmac
import io
import secrets
from functools import wraps

from flask import (Blueprint, Response, abort, current_app, redirect, render_template,
                   request, session, url_for)

from . import get_db

bp = Blueprint("admin", __name__, url_prefix="/admin")
STATUSES = ("new", "called", "demo", "won", "lost")


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(24)
    return session["csrf"]


def check_csrf():
    token = session.get("csrf", "")
    if not token or not hmac.compare_digest(request.form.get("csrf", ""), token):
        abort(400)


def login_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        if not session.get("admin"):
            return redirect(url_for("admin.login"))
        return fn(*a, **kw)
    return wrapper


@bp.route("/login", methods=["GET", "POST"])
def login():
    error = False
    if request.method == "POST":
        check_csrf()
        cfg = current_app.config
        ok_user = hmac.compare_digest(request.form.get("user", ""), cfg["ADMIN_USER"])
        ok_pass = bool(cfg["ADMIN_PASSWORD"]) and hmac.compare_digest(request.form.get("password", ""), cfg["ADMIN_PASSWORD"])
        if ok_user and ok_pass:
            session.clear()
            session["admin"] = True
            return redirect(url_for("admin.index"))
        error = True
    return render_template("admin/login.html", error=error, csrf=csrf_token())


@bp.post("/logout")
@login_required
def logout():
    check_csrf()
    session.clear()
    return redirect(url_for("admin.login"))


@bp.route("/")
@login_required
def index():
    rows = get_db().execute("SELECT * FROM leads ORDER BY id DESC LIMIT 500").fetchall()
    return render_template("admin/index.html", rows=rows, statuses=STATUSES, csrf=csrf_token())


@bp.post("/lead/<int:lead_id>")
@login_required
def set_status(lead_id):
    check_csrf()
    status = request.form.get("status")
    if status in STATUSES:
        db = get_db()
        db.execute("UPDATE leads SET status=? WHERE id=?", (status, lead_id))
        db.commit()
    return redirect(url_for("admin.index"))


@bp.route("/leads.csv")
@login_required
def export():
    rows = get_db().execute("SELECT id,ts,name,business,phone,message,source,lang,status FROM leads ORDER BY id").fetchall()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "ts", "name", "business", "phone", "message", "source", "lang", "status"])
    w.writerows([tuple(r) for r in rows])
    return Response("﻿" + buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=otto-leads.csv"})
