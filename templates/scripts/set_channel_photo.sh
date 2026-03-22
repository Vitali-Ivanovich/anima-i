#!/bin/bash
# set_channel_photo.sh — установка фото Telegram-канала
# Использование: bash set_channel_photo.sh /путь/к/фото.jpg
# Использует TELEGRAM_BOT_TOKEN и TELEGRAM_CHANNEL_ID из окружения

BOT_TOKEN="${TELEGRAM_BOT_TOKEN}"
CHANNEL_ID="${TELEGRAM_CHANNEL_ID}"
PHOTO="$1"

if [[ -z "$BOT_TOKEN" ]]; then
  echo "❌ TELEGRAM_BOT_TOKEN не задан" >&2
  exit 1
fi

if [[ -z "$CHANNEL_ID" ]]; then
  echo "❌ TELEGRAM_CHANNEL_ID не задан" >&2
  exit 1
fi

if [[ -z "$PHOTO" || ! -f "$PHOTO" ]]; then
  echo "❌ Файл изображения не найден: $PHOTO" >&2
  exit 1
fi

RESPONSE=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/setChatPhoto" \
  -F chat_id="${CHANNEL_ID}" \
  -F photo="@${PHOTO}")

OK=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('ok','false'))")

if [[ "$OK" == "True" ]]; then
  echo "✅ Фото канала обновлено"
else
  echo "❌ Ошибка: $RESPONSE" >&2
  exit 1
fi
