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

# Добавляем новый элемент в очередь через Python (с file locking)
LOCK_FILE="$SCRIPT_DIR/.generation_queue.lock"
python3 << PYEOF
import json, fcntl

queue_file = "$QUEUE_FILE"
lock_file = "$LOCK_FILE"

# File lock — защита от race condition с telegram_bot.py
with open(lock_file, "a") as lock_fd:
    fcntl.flock(lock_fd, fcntl.LOCK_EX)
    try:
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
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)

print("✅ Цель добавлена в очередь")
PYEOF
