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

## Полное демо для реального бизнеса (то, с чем идём продавать)

Цель: владелец открывает ссылку и видит **свой** сайт, готовый к запуску. Собирается за 30–40 минут.

1. **Данные (10 мин)** из Google Maps, Facebook, Instagram: точное название, адрес, телефон, часы,
   услуги и цены (если нет, берём типичные для ниши и помечаем в YAML `# уточнить`), 3 реальных отзыва из Google.
2. **Фото**: их собственные из Google Maps/Instagram → `static/img/<slug>-*.webp` (только для этого демо).
   Если фото плохие, бери CC0 из Openverse по нише.
3. **Логотип**: если у них нет нормального, рисуем свой вариант → `static/logos/<slug>.svg`, в YAML `logo: "<slug>.svg"`.
   Новый логотип продаёт лучше копии старого: «вот как может выглядеть ваш бренд».
4. **YAML**: `showcase: false`, `demo_for: "<название>"`, телефон и Viber — **их** настоящие.
5. `python build.py && python shots.py` → проверить на телефоне → push → ссылка во Viber.
6. Попросили удалить → удалить YAML и картинки, push.

Демо всегда `noindex` и с плашкой «примерен сайт … не е официален» (это делает шаблон).

## Локально

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python build.py --serve
```

## v3: сайт студии (Flask)

```bash
cp .env.example .env          # пароль админки, Telegram-бот
make test                     # pytest
make shots                    # скриншоты демо → static/shots/
make up                       # docker compose: app + nginx на :8080, проверка /health
```

Тексты страниц: `app/i18n/{bg,en,ru}.yaml`. Работы: `app/works.yaml`. Демо: `custom/<slug>/index.html` → `/demo/<slug>/`.
Заявки: `/admin/` (логин из `.env`), база `data/otto.db`, бэкап `make backup`. Дизайн-система: `DESIGN.md`.
