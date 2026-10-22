"""/admin/: учёт студии. Сделки по этапам, деньги (приход и расход), часы по сделке и дневные контакты.
Всё в той же SQLite, что заявки (data/otto.db, не в git). Отчёт за неделю: воронка, деньги, € в час."""
from datetime import date, timedelta

from flask import Blueprint, redirect, render_template, request, url_for

from . import get_db
from .admin import check_csrf, csrf_token, login_required

bp = Blueprint("ledger", __name__, url_prefix="/admin")
STAGES = [("contact", "Контакт"), ("show", "«Покажи»"), ("demo", "Демо отправлено"), ("meeting", "Встреча"),
          ("contract", "Договор"), ("paid", "Оплачено"), ("done", "Сдано"), ("lost", "Отказ")]
PACKAGES = [("", "—"), ("vizitka", "Визитка 79 €"), ("biznes", "Бизнес 149 €"), ("biznes_plus", "Бизнес+ 249 €"),
            ("grizha", "Грижа 15 €/мес."), ("extra", "Доп. работа")]
CATEGORIES_IN = ["оплата сайта", "аванс", "грижа за сайта", "другое"]
CATEGORIES_OUT = ["сервер", "домен", "печать", "транспорт", "реклама", "другое"]


def num(v, default=0.0):
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return default


@bp.route("/deals", methods=["GET", "POST"])
@login_required
def deals():
    db = get_db()
    if request.method == "POST":
        check_csrf()
        f = request.form
        if f.get("venue", "").strip():
            db.execute("INSERT INTO deals(venue,phone,channel,stage,package,price,next_step,next_date) VALUES(?,?,?,?,?,?,?,?)",
                       (f["venue"].strip()[:120], f.get("phone", "")[:40], f.get("channel", "")[:40], f.get("stage", "contact"),
                        f.get("package", ""), num(f.get("price")), f.get("next_step", "")[:200], f.get("next_date", "")[:10]))
            db.commit()
        return redirect(url_for("ledger.deals"))
    rows = db.execute("""SELECT d.*, COALESCE((SELECT SUM(hours) FROM hours h WHERE h.deal_id=d.id),0) AS h,
                         COALESCE((SELECT SUM(amount) FROM money m WHERE m.deal_id=d.id AND kind='in'),0) AS got
                         FROM deals d ORDER BY CASE stage WHEN 'lost' THEN 2 WHEN 'done' THEN 1 ELSE 0 END, next_date='', next_date, id DESC""").fetchall()
    return render_template("admin/deals.html", rows=rows, stages=STAGES, packages=PACKAGES, csrf=csrf_token(), today=date.today().isoformat())


@bp.post("/deals/<int:deal_id>")
@login_required
def deal_update(deal_id):
    check_csrf()
    f, db = request.form, get_db()
    if f.get("stage") in dict(STAGES):
        db.execute("UPDATE deals SET stage=?, updated=date('now') WHERE id=?", (f["stage"], deal_id))
    if "next_step" in f:
        db.execute("UPDATE deals SET next_step=?, next_date=?, updated=date('now') WHERE id=?",
                   (f.get("next_step", "")[:200], f.get("next_date", "")[:10], deal_id))
    if f.get("hours"):
        db.execute("INSERT INTO hours(deal_id,hours,what) VALUES(?,?,?)", (deal_id, num(f["hours"]), f.get("what", "")[:120]))
    db.commit()
    return redirect(url_for("ledger.deals"))


@bp.route("/money", methods=["GET", "POST"])
@login_required
def money():
    db = get_db()
    if request.method == "POST":
        check_csrf()
        f = request.form
        amount = num(f.get("amount"))
        if f.get("kind") in ("in", "out") and amount > 0:
            deal = int(f["deal_id"]) if f.get("deal_id", "").isdigit() else None
            db.execute("INSERT INTO money(day,kind,amount,category,deal_id,note) VALUES(?,?,?,?,?,?)",
                       (f.get("day") or date.today().isoformat(), f["kind"], amount, f.get("category", "")[:40], deal, f.get("note", "")[:200]))
            db.commit()
        return redirect(url_for("ledger.money"))
    rows = db.execute("SELECT m.*, d.venue FROM money m LEFT JOIN deals d ON d.id=m.deal_id ORDER BY day DESC, m.id DESC LIMIT 300").fetchall()
    months = db.execute("""SELECT substr(day,1,7) AS month, SUM(CASE kind WHEN 'in' THEN amount ELSE 0 END) AS got,
                           SUM(CASE kind WHEN 'out' THEN amount ELSE 0 END) AS spent FROM money GROUP BY month ORDER BY month DESC LIMIT 12""").fetchall()
    deals_ = db.execute("SELECT id, venue FROM deals WHERE stage!='lost' ORDER BY venue").fetchall()
    return render_template("admin/money.html", rows=rows, months=months, deals=deals_, cin=CATEGORIES_IN, cout=CATEGORIES_OUT,
                           csrf=csrf_token(), today=date.today().isoformat())


def week_report(db, weeks=6):
    """Понедельник–воскресенье: контакты, ответы, «покажи», оплаты, деньги, часы и € в час."""
    monday = date.today() - timedelta(days=date.today().weekday())
    out = []
    for k in range(weeks):
        a = monday - timedelta(weeks=k); b = a + timedelta(days=7); A, B = a.isoformat(), b.isoformat()
        act = db.execute("SELECT COALESCE(SUM(contacts),0), COALESCE(SUM(replies),0), COALESCE(SUM(shows),0) FROM activity WHERE day>=? AND day<?", (A, B)).fetchone()
        got = db.execute("SELECT COALESCE(SUM(amount),0) FROM money WHERE kind='in' AND day>=? AND day<?", (A, B)).fetchone()[0]
        spent = db.execute("SELECT COALESCE(SUM(amount),0) FROM money WHERE kind='out' AND day>=? AND day<?", (A, B)).fetchone()[0]
        hrs = db.execute("SELECT COALESCE(SUM(hours),0) FROM hours WHERE day>=? AND day<?", (A, B)).fetchone()[0]
        paid = db.execute("SELECT COUNT(*) FROM deals WHERE stage IN ('paid','done') AND updated>=? AND updated<?", (A, B)).fetchone()[0]
        out.append(dict(week=f"{a:%d.%m}–{(b - timedelta(days=1)):%d.%m}", contacts=act[0], replies=act[1], shows=act[2], paid=paid,
                        got=got, spent=spent, net=got - spent, hours=hrs, per_hour=(got - spent) / hrs if hrs else None))
    return out


@bp.route("/week", methods=["GET", "POST"])
@login_required
def week():
    db = get_db()
    if request.method == "POST":
        check_csrf()
        f = request.form
        day = f.get("day") or date.today().isoformat()
        db.execute("""INSERT INTO activity(day,contacts,replies,shows) VALUES(?,?,?,?)
                      ON CONFLICT(day) DO UPDATE SET contacts=excluded.contacts, replies=excluded.replies, shows=excluded.shows""",
                   (day[:10], int(num(f.get("contacts"))), int(num(f.get("replies"))), int(num(f.get("shows")))))
        db.commit()
        return redirect(url_for("ledger.week"))
    funnel = {s: db.execute("SELECT COUNT(*) FROM deals WHERE stage=?", (s,)).fetchone()[0] for s, _ in STAGES}
    today = db.execute("SELECT * FROM activity WHERE day=?", (date.today().isoformat(),)).fetchone()
    return render_template("admin/week.html", weeks=week_report(db), funnel=funnel, stages=STAGES, today_row=today,
                           csrf=csrf_token(), today=date.today().isoformat())
