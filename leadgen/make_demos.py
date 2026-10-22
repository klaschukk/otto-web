"""Личные демо для лидов: данные из карточки Google Maps → сайт заведения на /demo/<slug>/.
Вход:  leadgen/data/leads.json: только данные заведения (название, тип, адрес, телефон, рейтинг, число отзывов, часы).
       Чужие фото и тексты отзывов с именами авторов не берём: это персональные данные и чужой контент.
Выход: leads_demos/<slug>/index.html + img/, build.py копирует их в site/demo/. Обе папки данных не в git.
Запуск: .venv/bin/python leadgen/make_demos.py && .venv/bin/python build.py && make up"""
import html, json, re, sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parent.parent
DATA, OUT = ROOT / "leadgen" / "data", ROOT / "leads_demos"
BASE = "https://otto-web.online/demo/"
TR = dict(zip("абвгдежзийклмнопрстуфхцчшщъьюя", "a b v g d e zh z i y k l m n o p r s t u f h ts ch sh sht a y yu ya".split()))
DAYS = ["понеделник", "вторник", "сряда", "четвъртък", "петък", "събота", "неделя"]
THEMES = {  # цвета и шрифты по типу заведения; шрифты только из static/fonts/demo
    "pizza":   dict(css="berber-studio", display='"Oswald","Arial Narrow",sans-serif', body='"PT Sans",system-ui,sans-serif', up=True,
                    bg="#fbf5ec", soft="#f1e6d6", ink="#2b1a14", muted="#6d5a4d", line="#e2d4be", accent="#b3261e", on="#fff", dark=False),
    "sea":     dict(css="bistro-kei", display='"Playfair Display",Georgia,serif', body='"Manrope",system-ui,sans-serif', up=False,
                    bg="#f3f6f7", soft="#e1ecef", ink="#0f2633", muted="#4b6170", line="#c9dbe0", accent="#0f5f7a", on="#fff", dark=False),
    "kitchen": dict(css="dental-morska", display='"Literata",Georgia,serif', body='"Golos Text",system-ui,sans-serif', up=False,
                    bg="#f7f3ea", soft="#ece4d3", ink="#23281c", muted="#5f604f", line="#dcd1bb", accent="#8a3f1c", on="#fff", dark=False),
    "bar":     dict(css="berber-studio", display='"Oswald","Arial Narrow",sans-serif', body='"PT Sans",system-ui,sans-serif', up=True,
                    bg="#141414", soft="#1f1f1f", ink="#f3ece0", muted="#b3a998", line="#34312c", accent="#e0a43a", on="#141414", dark=True),
    "grill":   dict(css="avto-profi", display='"Russo One","Arial Black",sans-serif', body='"Rubik",system-ui,sans-serif', up=True,
                    bg="#111214", soft="#1b1c1f", ink="#f2f2f2", muted="#a7a9ad", line="#2c2d31", accent="#ffc400", on="#111214", dark=True),
}


def theme_key(th):
    return next(k for k, v in THEMES.items() if v is th)


def theme_for(title, cat):
    s = (title + " " + cat).lower()
    if re.search(r"пиц|pizza", s): return "pizza"
    if re.search(r"риб|морск|fish|seafood|капитан", s): return "sea"
    if re.search(r"бургер|burger|kebap|кебап|дюнер|fitbox|грил", s): return "grill"
    if re.search(r"бирария|бар\b|bar\b|кафе|coffee|пъб|pub", s): return "bar"
    return "kitchen"


def slug(title):
    s = "".join(TR.get(c, c) for c in title.lower())
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:40] or "zavedenie"


def nice_name(t):
    t = t.split("|")[0].strip()
    return re.sub(r'"([^"]+)"', "„\\1“", t)


def local_phone(p):
    d = re.sub(r"\D", "", p)
    return ("0" + d[3:] if d.startswith("359") else d), d


def fmt_local(d):
    return f"{d[:3]} {d[3:6]} {d[6:]}" if len(d) == 10 else d


def parse_hours(rows):
    """'сряда8:00ч.–0:00ч.' → {2: [[480, 1440]]}; 'Затворено' → []."""
    out = {}
    for r in rows:
        day = next((i for i, d in enumerate(DAYS) if r.lower().startswith(d)), None)
        if day is None: continue
        rest = r[len(DAYS[day]):]
        if "24 часа" in rest: out[day] = [[0, 1440]]; continue
        spans = []
        for a, b in re.findall(r"(\d{1,2}:\d{2})\s*ч?\.?\s*[–-]\s*(\d{1,2}:\d{2})", rest):
            h1, m1 = map(int, a.split(":")); h2, m2 = map(int, b.split(":"))
            s, e = h1 * 60 + m1, h2 * 60 + m2
            spans.append([s, e if e > s else e + 1440])
        out[day] = spans
    return out


def hours_table(h):
    if not h: return []
    def txt(sp): return "Затворено" if not sp else ", ".join(f"{s // 60}:{s % 60:02d} – {(e % 1440) // 60}:{e % 60:02d}".replace(" – 0:00", " – 00:00") for s, e in sp)
    rows, i = [], 0
    while i < 7:
        j = i
        while j + 1 < 7 and txt(h.get(j + 1, [])) == txt(h.get(i, [])): j += 1
        name = DAYS[i].capitalize() + ("" if i == j else " – " + DAYS[j])
        rows.append((name, txt(h.get(i, [])))); i = j + 1
    return rows


def main():
    leads = json.loads((DATA / "leads.json").read_text(encoding="utf-8"))
    env = Environment(loader=FileSystemLoader(ROOT / "leadgen"), autoescape=True)
    tpl = env.get_template("demo.html.j2")
    OUT.mkdir(exist_ok=True); made = []
    for l in leads:
        name, sl = nice_name(l["title"]), slug(l["title"].split("|")[0])
        loc, dg = local_phone(l["phone"])
        th = THEMES[l.get("theme") or theme_for(l["title"], l["cat"])]
        hours = parse_hours(l.get("hours", []))
        o = OUT / sl; o.mkdir(parents=True, exist_ok=True)
        page = tpl.render(name=name, cat=l["cat"], addr=l["addr"], area=l["area"], phone_local=fmt_local(loc), dg=dg,
                          viber=l.get("viber") != "novb", rating=f'{l["rating"]:.1f}'.replace(".", ","), rev=l["rev"],
                          hours_rows=hours_table(hours), hours_json=json.dumps(hours), maps=l["href"], t=th, kind=theme_key(th))
        (o / "index.html").write_text(page, encoding="utf-8")
        made.append({"id": l["id"], "slug": sl, "url": BASE + sl + "/", "name": name})
        print(f"  {sl:40} {theme_key(th):8} часы {len(hours)}")
    (DATA / "made.json").write_text(json.dumps(made, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"готово: {len(made)} демо в leads_demos/")


if __name__ == "__main__":
    sys.exit(main())
