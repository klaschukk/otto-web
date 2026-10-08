# Otto.web

Сайт студии Otto.web и демо-сайты для малого бизнеса в Бургасе. Статический сайт: YAML → Jinja2 → HTML, деплой через GitHub Actions на GitHub Pages.

```
site.yaml               студия: телефон, цены, домен
demos/<slug>.yaml       один демо-сайт (тема: dark | blush | garage | clinic)
templates/              storefront, service (общий шаблон бизнеса), gallery, 404
static/                 otto.css (витрина), demo.css (темы демо)
.github/workflows/      сборка + smoke test + деплой на Pages
```

## Новый демо-сайт для конкретного бизнеса (~15 минут)

```bash
cp demos/salon.yaml demos/studio-ani.yaml   # взять ближайшую нишу
# поменять: name, area, tagline, services, hours, address, map_query
# showcase: false — чтобы не появился на главной
# demo_for: "Studio Ani" — плашка «примерен сайт за Studio Ani»
python build.py --serve                     # проверить на http://127.0.0.1:8000/demo/studio-ani/
git add demos/studio-ani.yaml && git commit -m "demo: studio-ani" && git push
```

Через ~1 минуту после пуша демо доступно по `<base_url>/demo/studio-ani/`.

## Локально

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python build.py --serve
```
