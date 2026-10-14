# Otto.web: короткие команды
GIT_SHA := $(shell git rev-parse --short HEAD 2>/dev/null || echo dev)

test:            ## тесты
	.venv/bin/python -m pytest -q

shots:           ## скриншоты демо для витрины (нужен chromium)
	.venv/bin/python build.py && .venv/bin/python shots.py

up:              ## собрать и запустить на :8080
	mkdir -p data && chown -R 10001:10001 data  # контейнер пишет в базу от uid 10001
	GIT_SHA=$(GIT_SHA) docker compose up -d --build --remove-orphans
	docker compose exec -T web nginx -s reload  # deploy/nginx.conf примонтирован: без reload правки не применяются
	@sleep 3; curl -fsS http://127.0.0.1:8080/health

domain:          ## от root: otto-web.online в host-nginx + HTTPS (после DNS в Namecheap)
	bash deploy/install-domain.sh

backup:          ## копия базы заявок (для cron)
	mkdir -p backups && sqlite3 data/otto.db ".backup backups/otto-$$(date +%F).db"

-include local.mk  # локальные пути (PW_NODE_PATH), не в репозитории
.PHONY: test shots up domain backup og http2

og:              ## картинки превью ссылок: static/og/*.png (главная bg/ru/en и посадочные)
	NODE_PATH=$(PW_NODE_PATH) .venv/bin/python social/og.py

http2:           ## от root: HTTP/2 для otto-web.online в host-nginx (бэкап, проверка, откат при ошибке)
	@f=/etc/nginx/sites-available/otto-web.online; grep -q 'http2 on;' $$f && { echo "уже включён"; exit 0; }; \
	cp $$f /root/otto-web.online.nginx.bak && sed -i '0,/^\s*server_name otto-web\.online.*;$$/s//&\n    http2 on;/' $$f && \
	if nginx -t; then systemctl reload nginx && echo "HTTP/2 включён"; else cp /root/otto-web.online.nginx.bak $$f; echo "ошибка, вернул как было"; exit 1; fi
