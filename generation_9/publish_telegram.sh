#!/bin/bash
# publish_telegram.sh — публикация поста агента в Telegram-канал
# Принимает текст поста через stdin или первый аргумент
# Использует TELEGRAM_BOT_TOKEN и TELEGRAM_CHANNEL_ID из окружения

BOT_TOKEN="${TELEGRAM_BOT_TOKEN}"
CHANNEL_ID="${TELEGRAM_CHANNEL_ID}"

if [[ -z "$BOT_TOKEN" ]]; then
  echo "❌ TELEGRAM_BOT_TOKEN не задан" >&2
  exit 1
fi

if [[ -z "$CHANNEL_ID" ]]; then
  echo "❌ TELEGRAM_CHANNEL_ID не задан" >&2
  exit 1
fi

# Читаем текст из аргумента или stdin
if [[ -n "$1" ]]; then
  TEXT="$1"
else
  TEXT="$(cat)"
fi

if [[ -z "$TEXT" ]]; then
  echo "❌ Текст поста пустой" >&2
  exit 1
fi

RESPONSE=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
  --data-urlencode "chat_id=${CHANNEL_ID}" \
  --data-urlencode "text=${TEXT}" \
  --data-urlencode "parse_mode=Markdown")

OK=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('ok','false'))")

if [[ "$OK" == "True" ]]; then
  echo "✅ Пост опубликован в ${CHANNEL_ID}"
else
  echo "❌ Ошибка публикации: $RESPONSE" >&2
  exit 1
fi
