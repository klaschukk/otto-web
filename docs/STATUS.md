# Otto.web — состояние (читать первым)

Обновлено: 2026-10-10. Этот файл — единственное, что нужно прочитать, чтобы продолжить работу. Подробности: `README.md` (команды), `DESIGN.md` (дизайн-система), `docs/V3_SPEC.md` (исходное ТЗ).

## Где что

| Что | Где |
|---|---|
| Живой сайт | https://otto-web.online (HTTPS Let's Encrypt, автопродление certbot) |
| Стек | Flask 3 + Jinja2 + gunicorn + SQLite в Docker Compose (`app` + `web` nginx на 127.0.0.1:8080), снаружи host-nginx |
| Страницы | `app/templates/*.html`, тексты `app/i18n/{bg,en,ru}.yaml`, стили `static/css/site.css`, JS `static/js/` |
| Работы | `app/works.yaml` (4 демо) + реальный клиент SARAFAN (блок `client:` в i18n) |
| Демо | `custom/<slug>/index.html` → `/demo/<slug>/` (ручные, один HTML на демо, noindex) |
| Заявки | `POST /api/lead` → `data/otto.db` + Telegram; список `/admin/` (логин в `.env`) |
| Секреты | `.env` (не в git): админка, Telegram, BASE_URL, OTTO_BIND, GOOGLE_SITE_VERIFICATION |
| Договор | шаблон `contract/dogovor.html` + `contract/firm.local.yaml` (не в git) → `python contract/render.py` → `contract/out/` |
| Лиды | `/home/site-studio/leads/` (вне репо) |
| Домен | Namecheap, otto-web.online до 09.10.2027, автопродление выключено (продление ~30–40 $) |

## Команды

```bash
make test      # pytest (37 тестов)
.venv/bin/python print/render.py   # листовка → print/out/listovka.pdf
make up        # пересобрать и перезапустить контейнеры, проверить /health
make shots     # скриншоты демо для витрины
make backup    # копия базы заявок
make domain    # ТОЛЬКО владелец от root: vhost + сертификат (уже выполнено 09.10)
```

После любой правки шаблонов, CSS, i18n или демо нужен `make up`: контейнер отдаёт файлы из образа.
Проверка скриншотом: `chromium --headless=new --no-sandbox --window-size=390,2000 --screenshot=out.png URL`.
Браузер gstack browse общий для всех сессий на сервере: для своих проверок брать отдельный headless chromium.

## Правила

- Коммиты маленькие, identity `klaschuk <178824815+klaschukk@users.noreply.github.com>`, без строк про ИИ-инструменты. Перед коммитом `git diff`.
- В репо (он публичный) не попадают: домашний адрес, IBAN, имя управителя, `.env`. На сайте о фирме: название + ЕИК + «гр. Бургас».
- Не выдумывать цифры, отзывы, клиентов. Демо помечены как демо, цены в демо примерные.
- Системный nginx, systemd и сертификаты меняет только владелец (готовим скрипт и make-цель).
- SARAFAN называть «детски клуб», не «детска градина».

## Сделано

- v3 сайт: главная, /raboti/ (+ кейсы), /ceni/ (калькулятор), /kontakt/, политика конфиденциальности, bg/en/ru, /admin/.
- 4 ручных демо: avto-profi (калькулятор), berber-studio (часы на сегодня), studio-mila (палитра лаков), dental-morska (карта зубов FDI).
- Форма → SQLite + Telegram (бот общий с prevozni, сообщения начинаются с «Otto.web · нова заявка»).
- Домен, HTTPS, редирект http→https, :8080 закрыт снаружи. Search Console подтверждён, sitemap отправлен.
- Почта info@otto-web.online → пересылка на Gmail (Namecheap).
- Договор: 6 страниц A4, реквизиты вне репо.

## Очередь

1. [x] QA сайта 10.10: 33 страницы × 390/768/1440 автоматически (горизонтальный скролл, битые картинки, ошибки JS, чужие запросы, мелкие кнопки и текст) — критичных проблем нет. Lighthouse mobile главной: 98 / 100 / 100 / 100. Форма, ловушка для ботов, калькулятор цен проверены в браузере.
2. [x] Лиды: `/home/site-studio/leads/OBHOD_SALONI.md` — 51 салон Бургаса с 20+ отзывами (studio24.bg) по районам, для обхода с листовкой. Каталоги и поиск телефонов почти не дают; для автосервисов и стоматологов нужен Google Maps через Claude в Chrome (промпт в README лидов).
3. [x] `docs/STRATEGY.md`.
4. [x] Листовка A4: `print/listovka.html` → `python print/render.py` → `print/out/listovka.pdf`. QR проверен декодированием с PDF (цвет и ч/б).
5. [x] Аналитика Umami: сайт заведён (id в `.env`), скрипт и события идут через наш домен `/u/…`, cookies нет. Панель: stats.flightpunctuality.online. Сканы QR видны по `utm_source=flyer`.
6. [x] Шрифты демо перенесены на свой сервер (`static/fonts/demo/`). Единственный чужой ресурс на сайте — карта Google в демо автосервиса, указана в политике.
7. [x] Демо: области нажатия в шапке и подвале увеличены.
9. [x] Заголовки безопасности: HSTS (только по HTTPS), CSP, Permissions-Policy; `/favicon.ico` и apple-touch-icon.
10. [x] Визуальный проход EN/RU и страницы кейса на телефоне: проблем нет. CSP: страницы студии строгие, для `/demo/` разрешены Google Fonts, карта и свои фреймы (шаблонные демо и демо для лидов).
8. [ ] Вычитка болгарских текстов носителем языка: сайт, листовка, скрипты в STRATEGY.md.

## Задачи для владельца (нужен root или аккаунт)

- HTTP/2 в системном nginx для otto-web.online: Lighthouse оценивает выигрыш ~0.5 с. В `/etc/nginx/sites-available/otto-web.online` строку `listen 443 ssl;` заменить на `listen 443 ssl http2;` (и то же для `[::]:443`), затем `nginx -t && systemctl reload nginx`.
- Распечатать `print/out/listovka.pdf` (A4, 100 %, цвет или ч/б).

## Вопросы владельцу

- Письмо на info@otto-web.online дошло до Gmail? Тогда меняем email на сайте.
- Фото лицом для блока «Кой стои зад Otto.web» (сейчас монограмма).
- Мама согласна, что SARAFAN показан как работа?
- Старый деплой на GitHub Pages (`.github/workflows`, job build-and-deploy) всё ещё публикует версию v2 на klaschukk.github.io/otto-web. Отключить? Рекомендация: да, это устаревший дубль сайта.
- Тексты сайта смешивают «аз» и «ние» («Правим сайтове…» и «Аз съм Кирил…»). Оставить так или перевести всё в «аз»?
- Цифры в блоке «Кой стои зад Otto.web» (~350 посетителей, 45 000 показов в день) взяты из CV, источник там — Search Console, сентябрь 2026. Обновлять при изменении.

## Журнал

- 10.10 ночь: QA, SEO-заголовки и описания страниц, листовка A4, стратегия, Umami через свой домен, сбор лидов (studio24, каталоги).
- 10.10 17:20: ночной цикл оборвался в 05:15 (перезапуск сессии), хвост доделан и закоммичен. За день в Umami 19 просмотров от 17 посетителей, сканов листовки 0, заявок 0.
