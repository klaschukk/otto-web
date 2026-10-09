# Otto.web: короткие команды
GIT_SHA := $(shell git rev-parse --short HEAD 2>/dev/null || echo dev)

test:            ## тесты
	.venv/bin/python -m pytest -q

shots:           ## скриншоты демо для витрины (нужен chromium)
	.venv/bin/python build.py && .venv/bin/python shots.py

up:              ## собрать и запустить на :8080
	mkdir -p data && chown -R 10001:10001 data  # контейнер пишет в базу от uid 10001
	GIT_SHA=$(GIT_SHA) docker compose up -d --build --remove-orphans
	@sleep 3; curl -fsS http://127.0.0.1:8080/health

domain:          ## от root: otto-web.online в host-nginx + HTTPS (после DNS в Namecheap)
	bash deploy/install-domain.sh

backup:          ## копия базы заявок (для cron)
	mkdir -p backups && sqlite3 data/otto.db ".backup backups/otto-$$(date +%F).db"

.PHONY: test shots up domain backup
