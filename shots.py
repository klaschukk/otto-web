#!/usr/bin/env python3
"""Скриншоты демо для витрины: static/shots/<slug>.webp (телефон 390x844 @2x).

Запускать локально после изменений демо: python build.py && python shots.py
Нужен chromium; сайт берётся из site/ через временный http-сервер.
"""
import functools, http.server, subprocess, tempfile, threading
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).parent
SITE, OUT = ROOT / "site", ROOT / "static" / "shots"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    handler = functools.partial(Quiet, directory=str(SITE))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    slugs = [p.parent.name for p in sorted(SITE.glob("demo/*/index.html"))]
    for slug in slugs:
        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "s.png"
            subprocess.run(["chromium", "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                            "--force-device-scale-factor=2", "--window-size=390,844", "--virtual-time-budget=5000",
                            f"--screenshot={png}", f"http://127.0.0.1:{port}/demo/{slug}/?shot=1"],
                           check=True, capture_output=True)
            Image.open(png).convert("RGB").save(OUT / f"{slug}.webp", "WEBP", quality=78, method=6)
        print(f"  shots/{slug}.webp")
    srv.shutdown()


if __name__ == "__main__":
    main()
