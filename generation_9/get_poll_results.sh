#!/bin/bash
# get_poll_results.sh — чтение результатов опроса через stopPoll
# Использование: ./get_poll_results.sh [--stop]
# Без --stop: показывает текущее состояние (из poll_state.json)
# С --stop: закрывает опрос и получает финальные результаты

BOT_TOKEN="${TELEGRAM_BOT_TOKEN}"
CHANNEL_ID="${TELEGRAM_CHANNEL_ID}"
POLL_STATE="/home/docsgpt/anima-i/generation_9/poll_state.json"

if [[ -z "$BOT_TOKEN" ]]; then
  echo "❌ TELEGRAM_BOT_TOKEN не задан" >&2
  exit 1
fi

if [[ ! -f "$POLL_STATE" ]]; then
  echo "❌ Нет активного опроса (файл $POLL_STATE не найден)" >&2
  exit 1
fi

MSG_ID=$(python3 -c "import json; print(json.load(open('$POLL_STATE'))['message_id'])")
QUESTION=$(python3 -c "import json; print(json.load(open('$POLL_STATE'))['question'])")

echo "📊 Опрос: $QUESTION"
echo "📌 message_id: $MSG_ID"
echo ""

if [[ "$1" == "--stop" ]]; then
  echo "🔒 Закрываю опрос и получаю финальные результаты..."

  RESPONSE=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/stopPoll" \
    --data-urlencode "chat_id=${CHANNEL_ID}" \
    --data-urlencode "message_id=${MSG_ID}")

  OK=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('ok','false'))")

  if [[ "$OK" == "True" ]]; then
    echo "✅ Опрос закрыт. Результаты:"
    echo ""

    # Парсим и выводим результаты
    python3 -c "
import json, sys

response = json.loads('''$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin)))")''')
poll = response['result']

total = poll['total_voter_count']
print(f'Всего голосов: {total}')
print()

for opt in poll['options']:
    text = opt['text']
    count = opt['voter_count']
    pct = (count / total * 100) if total > 0 else 0
    bar = '█' * int(pct / 5) + '░' * (20 - int(pct / 5))
    print(f'  {text}')
    print(f'  {bar} {count} ({pct:.0f}%)')
    print()

# Сохраняем результаты
with open('$POLL_STATE', 'r') as f:
    state = json.load(f)
state['status'] = 'closed'
state['total_votes'] = total
state['results'] = [{'text': o['text'], 'votes': o['voter_count']} for o in poll['options']]
with open('$POLL_STATE', 'w') as f:
    json.dump(state, f, ensure_ascii=False, indent=2)
print('📁 Результаты сохранены в $POLL_STATE')
"
  else
    echo "❌ Ошибка: $RESPONSE" >&2

    # Может уже закрыт — попробуем прочитать из state
    echo ""
    echo "Попробую показать последнее известное состояние..."
    python3 -c "
import json
with open('$POLL_STATE') as f:
    state = json.load(f)
if 'results' in state:
    print('Последние результаты:')
    for r in state['results']:
        print(f\"  {r['text']}: {r['votes']} голосов\")
else:
    print('Результатов пока нет.')
"
    exit 1
  fi
else
  echo "ℹ️  Опрос активен. Для закрытия и получения результатов: $0 --stop"
  echo ""
  python3 -c "
import json
with open('$POLL_STATE') as f:
    state = json.load(f)
print(f\"Отправлен: {state['sent_at']}\")
print(f\"Статус: {state['status']}\")
if 'results' in state:
    for r in state['results']:
        print(f\"  {r['text']}: {r['votes']} голосов\")
"
fi
