#!/bin/bash
# Подключить otto-web.online к контейнеру: vhost в host-nginx + сертификат Let's Encrypt.
# Запуск от root, когда A-записи в Namecheap уже смотрят на сервер:  make domain
set -euo pipefail
D=otto-web.online
IP=159.195.196.170
cd "$(dirname "$0")/.."

for h in "$D" "www.$D"; do
  got=$(dig +short A "$h" @1.1.1.1 | tail -1)
  if [ "$got" != "$IP" ]; then
    echo "DNS: $h -> '${got:-пусто}', а нужно $IP. Проверь записи в Namecheap, подожди 5–30 минут и запусти снова."
    exit 1
  fi
done

# повторный запуск не затирает блок 443, который дописал certbot
if [ ! -e /etc/nginx/sites-available/$D ]; then
  install -m 644 deploy/host-nginx/$D.conf /etc/nginx/sites-available/$D
fi
ln -sf /etc/nginx/sites-available/$D /etc/nginx/sites-enabled/$D
nginx -t
systemctl reload nginx

certbot --nginx -d "$D" -d "www.$D" --redirect --non-interactive --agree-tos --register-unsafely-without-email

# дальше сайт только через домен: ссылки на https, контейнер слушает только localhost, временное правило ufw убираем
sed -i -e '/^BASE_URL=/d' -e '/^OTTO_BIND=/d' .env
printf 'BASE_URL=https://%s\nOTTO_BIND=127.0.0.1\n' "$D" >> .env
make up
ufw delete allow 8080/tcp >/dev/null 2>&1 || true
sleep 2
curl -fsS "https://$D/health" && echo "Готово: https://$D"
