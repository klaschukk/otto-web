import re
import sqlite3

import pytest

PAGES = ["/", "/raboti/", "/raboti/avto-profi/", "/raboti/dental-morska/", "/ceni/", "/kontakt/", "/blagodarim/", "/poveritelnost/"]


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
    assert "/en/ceni/" in client.get("/sitemap.xml").get_data(as_text=True)


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
