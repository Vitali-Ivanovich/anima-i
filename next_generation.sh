#!/bin/bash
# next_generation.sh — постановка цели следующего поколения в очередь
# Использование: bash next_generation.sh "предлагаемая цель" [source]
# source: mefodiy (по умолчанию) или operator

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
QUEUE_FILE="$SCRIPT_DIR/.generation_queue.json"
GOAL="${1}"
SOURCE="${2:-mefodiy}"

if [[ -z "$GOAL" ]]; then
    echo "❌ Цель не указана" >&2
    exit 1
fi

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Создаём очередь если не существует
if [[ ! -f "$QUEUE_FILE" ]]; then
    echo '{"queue": []}' > "$QUEUE_FILE"
fi

# Добавляем новый элемент в очередь через Python
python3 << PYEOF
import json, sys

queue_file = "$QUEUE_FILE"
with open(queue_file, 'r') as f:
    data = json.load(f)

data['queue'].append({
    "goal": """$GOAL""",
    "source": "$SOURCE",
    "status": "pending_approval",
    "start_time": None,
    "proposed_at": "$TIMESTAMP"
})

with open(queue_file, 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("✅ Цель добавлена в очередь")
PYEOF
