import re
import sqlite3

import pytest

PAGES = ["/", "/raboti/", "/raboti/avto-profi/", "/raboti/dental-morska/", "/ceni/", "/kontakt/", "/blagodarim/", "/poveritelnost/",
         "/sait-za-restorant/", "/sait-za-salon/", "/sait-za-avtoservis/", "/sait-za-barbershop/", "/sait-za-zabolekar/",
         "/izrabotka-na-sait-nesebar/", "/izrabotka-na-sait-slanchev-bryag/", "/izrabotka-na-sait-pomorie/", "/izrabotka-na-sait-sozopol/", "/izrabotka-na-sait-primorsko/"]


@pytest.mark.parametrize("prefix", ["", "/en", "/ru"])
@pytest.mark.parametrize("path", PAGES)
def test_pages_200(client, prefix, path):
    r = client.get(prefix + path)
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert "{{" not in html and "hreflang=\"ru\"" in html


def test_404(client):
    assert client.get("/raboti/no-such/").status_code == 404
    assert client.get("/nope/").status_code == 404


def test_health_robots_sitemap(client):
    assert client.get("/health").get_data(as_text=True).startswith("ok")
    assert "Disallow: /demo/" in client.get("/robots.txt").get_data(as_text=True)
    sm = client.get("/sitemap.xml").get_data(as_text=True)
    assert "/en/ceni/" in sm and "/ru/sait-za-restorant/" in sm


@pytest.mark.parametrize("prefix", ["", "/en", "/ru"])
def test_home_story_has_six_steps(client, prefix):
    html = client.get(prefix + "/").get_data(as_text=True)
    assert html.count('class="sx-step"') == 6 and 'data-s="5"' in html and "ba-stage" not in html


def test_landing_has_faq_and_service_markup(client):
    html = client.get("/sait-za-restorant/").get_data(as_text=True)
    assert '"FAQPage"' in html and '"Service"' in html and '"price": "79"' in html
    assert html.count("<h1") == 1 and "/sait-za-salon/" in html and "/demo/bistro-kei/" in html
    assert "/sait-za-restorant/" in client.get("/raboti/bistro-kei/").get_data(as_text=True)


def count(app):
    con = sqlite3.connect(app.config["DB_PATH"])
    n = con.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    con.close()
    return n


def lead(client, **kw):
    data = {"name": "Мария", "business": "Салон", "phone": "0888 123 456", "lang": "bg", "source": "home"}
    data.update(kw)
    return client.post("/api/lead", data=data, headers={"Accept": "application/json"})


def test_lead_saved(client, app):
    r = lead(client)
    assert r.status_code == 200 and r.json["ok"]
    assert count(app) == 1


def test_lead_without_js_redirects_to_thanks(client, app):
    r = client.post("/api/lead", data={"name": "Ivan", "phone": "0888123456", "lang": "en"})
    assert r.status_code == 303 and r.headers["Location"].endswith("/en/blagodarim/")


def test_lead_validation(client, app):
    r = lead(client, name="", phone="12")
    assert r.status_code == 400 and set(r.json["errors"]) == {"name", "phone"}
    assert count(app) == 0


def test_honeypot_blocks_bots(client, app):
    r = lead(client, website="http://spam.example")
    assert r.status_code == 200  # бот думает, что всё ок
    assert count(app) == 0


def test_seo_spam_is_kept_quietly(client, app):
    r = lead(client, name="Ted Ferretti", business="", phone="+1 283 555 0101", message="List your site in Google's Search Index")
    assert r.status_code == 200
    lead(client, name="Ivan", business="", phone="0888 123 456", message="hi")  # болгарский номер латиницей: не спам
    con = sqlite3.connect(app.config["DB_PATH"])
    rows = con.execute("SELECT name, status FROM leads ORDER BY id").fetchall()
    con.close()
    assert rows == [("Ted Ferretti", "spam"), ("Ivan", "new")]


def test_rate_limit(client, app):
    for _ in range(5):
        assert lead(client).status_code == 200
    assert lead(client).status_code == 429
    assert count(app) == 5


def csrf_of(client, url):
    return re.search(r'name="csrf" value="([^"]+)"', client.get(url).get_data(as_text=True)).group(1)


def test_admin_requires_login(client):
    r = client.get("/admin/")
    assert r.status_code == 302 and "/admin/login" in r.headers["Location"]
    assert client.get("/admin/leads.csv").status_code == 302


def test_admin_login_and_list(client):
    lead(client, name="Петър")
    token = csrf_of(client, "/admin/login")
    bad = client.post("/admin/login", data={"user": "admin", "password": "wrong", "csrf": token})
    assert "Неверный" in bad.get_data(as_text=True)
    ok = client.post("/admin/login", data={"user": "admin", "password": "secret-pass", "csrf": token})
    assert ok.status_code == 302
    page = client.get("/admin/").get_data(as_text=True)
    assert "Петър" in page
    assert "Петър" in client.get("/admin/leads.csv").get_data(as_text=True)


def test_admin_login_needs_csrf(client):
    assert client.post("/admin/login", data={"user": "admin", "password": "secret-pass"}).status_code == 400


def test_no_third_party_assets_on_studio_pages(client):
    html = client.get("/").get_data(as_text=True)
    for host in ("fonts.googleapis.com", "fonts.gstatic.com", "cdnjs.cloudflare.com", "openstreetmap.org"):
        assert host not in html


def test_privacy_has_controller_but_no_address(client):
    html = client.get("/poveritelnost/").get_data(as_text=True)
    assert "ЕИК" in html and "{company}" not in html and "Сарафово" not in html


def test_favicon_ico_is_served(client):
    r = client.get("/favicon.ico")
    assert r.status_code == 200
    assert r.data[:4] == b"\x00\x00\x01\x00"  # заголовок ICO



def login(client):
    token = csrf_of(client, "/admin/login")
    client.post("/admin/login", data={"user": "admin", "password": "secret-pass", "csrf": token})
    return csrf_of(client, "/admin/deals")


def test_ledger_requires_login(client):
    for p in ("/admin/deals", "/admin/money", "/admin/week"):
        assert client.get(p).status_code == 302


def test_ledger_deal_money_hours_and_week(client):
    t = login(client)
    client.post("/admin/deals", data={"csrf": t, "venue": "Тест бистро", "stage": "show", "package": "biznes", "price": "149"})
    page = client.get("/admin/deals").get_data(as_text=True)
    assert "Тест бистро" in page
    client.post("/admin/deals/1", data={"csrf": t, "stage": "paid"})
    client.post("/admin/deals/1", data={"csrf": t, "hours": "5", "what": "сборка"})
    client.post("/admin/money", data={"csrf": t, "kind": "in", "amount": "149", "category": "оплата сайта", "deal_id": "1"})
    client.post("/admin/money", data={"csrf": t, "kind": "out", "amount": "9,5", "category": "сервер"})
    client.post("/admin/week", data={"csrf": t, "contacts": "12", "replies": "3", "shows": "1"})
    week = client.get("/admin/week").get_data(as_text=True)
    assert "<b>140</b>" in week and ">12<" in week and "27.9" in week  # итог 149−9,5 ≈ 140; € в час (149−9,5)/5
    assert "29.8" in client.get("/admin/deals").get_data(as_text=True)  # 149/5 по сделке


def test_articles_bg_only(client):
    for p in ("/polezno/", "/polezno/menu-v-google-maps/", "/polezno/qr-menu-za-restorant/", "/polezno/kolko-struva-sait-za-restorant/"):
        html = client.get(p).get_data(as_text=True)
        assert "{{" not in html and 'hreflang="ru"' not in html
    assert '"Article"' in client.get("/polezno/menu-v-google-maps/").get_data(as_text=True)
    assert client.get("/polezno/nope/").status_code == 404
    assert "/polezno/qr-menu-za-restorant/" in client.get("/sitemap.xml").get_data(as_text=True)
