#!/bin/bash
# send_poll.sh — отправка опроса в Telegram-канал
# Использование: ./send_poll.sh "Вопрос" "Вариант 1" "Вариант 2" ["Вариант 3" ...]
# Опционально: POLL_ANONYMOUS=false для неанонимного опроса
# Сохраняет message_id в poll_state.json для последующего чтения результатов

BOT_TOKEN="${TELEGRAM_BOT_TOKEN}"
CHANNEL_ID="${TELEGRAM_CHANNEL_ID}"
POLL_STATE="/home/docsgpt/anima-i/generation_9/poll_state.json"

if [[ -z "$BOT_TOKEN" ]]; then
  echo "❌ TELEGRAM_BOT_TOKEN не задан" >&2
  exit 1
fi

if [[ -z "$CHANNEL_ID" ]]; then
  echo "❌ TELEGRAM_CHANNEL_ID не задан" >&2
  exit 1
fi

if [[ $# -lt 3 ]]; then
  echo "❌ Нужен вопрос и минимум 2 варианта ответа" >&2
  echo "Использование: $0 \"Вопрос\" \"Вариант 1\" \"Вариант 2\" [...]" >&2
  exit 1
fi

QUESTION="$1"
shift

# Формируем JSON-массив вариантов
OPTIONS=$(python3 -c "
import json, sys
options = sys.argv[1:]
print(json.dumps(options, ensure_ascii=False))
" "$@")

IS_ANONYMOUS="${POLL_ANONYMOUS:-true}"

RESPONSE=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/sendPoll" \
  --data-urlencode "chat_id=${CHANNEL_ID}" \
  --data-urlencode "question=${QUESTION}" \
  --data-urlencode "options=${OPTIONS}" \
  --data-urlencode "is_anonymous=${IS_ANONYMOUS}" \
  --data-urlencode "allows_multiple_answers=false")

OK=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('ok','false'))")

if [[ "$OK" == "True" ]]; then
  # Сохраняем данные опроса для последующего чтения
  MSG_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['message_id'])")
  POLL_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['poll']['id'])")

  python3 -c "
import json
from datetime import datetime
state = {
    'message_id': $MSG_ID,
    'poll_id': '$POLL_ID',
    'question': '''$QUESTION''',
    'options': $OPTIONS,
    'sent_at': datetime.now().isoformat(),
    'status': 'active'
}
with open('$POLL_STATE', 'w') as f:
    json.dump(state, f, ensure_ascii=False, indent=2)
"

  echo "✅ Опрос отправлен! message_id=$MSG_ID, poll_id=$POLL_ID"
  echo "📁 Состояние сохранено в $POLL_STATE"
else
  echo "❌ Ошибка отправки опроса: $RESPONSE" >&2
  exit 1
fi
