#!/usr/bin/env bash
# tunnel.sh — РУЧНОЙ запуск serveo-туннеля к Mini App (альтернатива встроенному в бота).
#
# Обычно НЕ нужен: при TUNNEL_ENABLED=true бот сам поднимает туннель и ставит кнопку меню.
# Этот скрипт — на случай, если хочешь держать туннель отдельным процессом.
#
# Запускать ИЗНУТРИ proot (там же, где бот):  bash /root/quiz_bot_new/tunnel.sh
#
# cloudflared на этой сети заблокирован DPI — поэтому serveo (SSH).

set -e
PORT="${WEBAPP_PORT:-8080}"
DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$DIR/.env"
LOG="$DIR/tunnel.log"
KEY="/root/.ssh/serveo_ed25519"
SUB="${TUNNEL_SUBDOMAIN:-}"   # непусто → постоянный поддомен (нужен зарегистр. ключ)

REMOTE="80:localhost:$PORT"
[ -n "$SUB" ] && REMOTE="$SUB:80:localhost:$PORT"
KEYOPT=""; [ -f "$KEY" ] && KEYOPT="-i $KEY"

: > "$LOG"
# shellcheck disable=SC2086
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes \
    $KEYOPT -R "$REMOTE" serveo.net >>"$LOG" 2>&1 &
TUN_PID=$!

URL=""
for i in $(seq 1 30); do
  URL=$(grep -iE 'forwarding' "$LOG" | grep -oE 'https://[A-Za-z0-9.-]+\.serveo(usercontent)?\.(net|com)' \
        | grep -v 'console.serveo.net' | head -n1 || true)
  [ -n "$URL" ] && break
  kill -0 "$TUN_PID" 2>/dev/null || break
  sleep 1
done

if [ -z "$URL" ]; then
  echo "Не удалось получить URL. Смотри $LOG"; kill "$TUN_PID" 2>/dev/null || true; exit 1
fi
FULL="$URL/?serveo-skip-browser-warning=true"
echo "Туннель: $FULL  (pid $TUN_PID)"

if grep -q '^WEBAPP_URL=' "$ENV_FILE"; then
  sed -i "s|^WEBAPP_URL=.*|WEBAPP_URL=$FULL|" "$ENV_FILE"
else
  echo "WEBAPP_URL=$FULL" >> "$ENV_FILE"
fi
echo "WEBAPP_URL прописан в .env. Если используешь ручной режим — выключи TUNNEL_ENABLED и перезапусти бота."
echo "Оставь терминал открытым — туннель живёт, пока работает ssh."
wait "$TUN_PID"
