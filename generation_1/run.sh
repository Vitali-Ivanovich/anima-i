#!/bin/bash
# run.sh — Запуск одного шага агента Мефодий
# Собирает контекст из md-файлов, передаёт в claude, публикует результат в Telegram

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENTS_MD="$SCRIPT_DIR/AGENTS.md"
RUNTIME_DIR="$SCRIPT_DIR/.runtime"
RUNTIME_LOG_DIR="$RUNTIME_DIR/logs"
CRASH_LOG="$RUNTIME_DIR/crash_events.md"
PENDING_CRASH="$RUNTIME_DIR/pending_crash.md"

mkdir -p "$RUNTIME_LOG_DIR"
touch "$CRASH_LOG"

# Проверка обязательных файлов
if [[ ! -f "$AGENTS_MD" ]]; then
    echo "❌ Файл AGENTS.md не найден в $SCRIPT_DIR"
    exit 1
fi

if [[ ! -f "$SCRIPT_DIR/MAIN_GOAL.md" ]]; then
    echo "❌ Файл MAIN_GOAL.md не найден в $SCRIPT_DIR"
    exit 1
fi

# Подсчёт состояния TODO и INBOX
TODO_OPEN_COUNT=$(grep -cE '^\s*-\s*\[\s\]\s+' "$SCRIPT_DIR/TODO.md" 2>/dev/null; [ "${PIPESTATUS[0]}" -le 1 ] || true)
TODO_DONE_COUNT=$(grep -cE '^\s*-\s*\[[xX]\]\s+' "$SCRIPT_DIR/TODO.md" 2>/dev/null; true)
UNREAD_MESSAGE_COUNT=$(sed -n '/## Непрочитанные/,/^## /p' "$SCRIPT_DIR/INBOX.md" 2>/dev/null | grep -c '^### '; true)

TODO_OPEN_COUNT=${TODO_OPEN_COUNT:-0}
TODO_DONE_COUNT=${TODO_DONE_COUNT:-0}
UNREAD_MESSAGE_COUNT=${UNREAD_MESSAGE_COUNT:-0}

REPLAN_REQUESTED=0
if [[ "${AUTO_AGENT_REPLAN:-0}" == "1" || "${AUTO_AGENT_FORCE_NEXT_CYCLE:-0}" == "1" ]]; then
    REPLAN_REQUESTED=1
fi

if [[ "$TODO_OPEN_COUNT" -gt 0 ]]; then
    TODO_CYCLE_STATUS="active"
elif [[ "$TODO_DONE_COUNT" -gt 0 ]]; then
    TODO_CYCLE_STATUS="completed"
else
    TODO_CYCLE_STATUS="empty"
fi

RUNTIME_INCIDENT_PRESENT=0
[[ -s "$PENDING_CRASH" ]] && RUNTIME_INCIDENT_PRESENT=1

# Запись инцидента при аварийном завершении
record_runtime_incident() {
    local reason="$1"
    local exit_code="$2"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S %z')

    cat >> "$CRASH_LOG" <<INCIDENT
## $timestamp
- exit_code: $exit_code
- reason: $reason
- todo_cycle_status: $TODO_CYCLE_STATUS
INCIDENT

    cat > "$PENDING_CRASH" <<PENDING
## Незавершённый предыдущий запуск
- timestamp: $timestamp
- exit_code: $exit_code
- reason: $reason
- todo_cycle_status: $TODO_CYCLE_STATUS

Сначала коротко осмысли причину сбоя, зафикисруй в MEMORY.md/JOURNAL.md, затем продолжи обычный цикл.
PENDING
}

# Сборка контекста пробуждения
PROMPT="# Main Goal
$(cat "$SCRIPT_DIR/MAIN_GOAL.md")

---

# Моя память (MEMORY.md)
$(cat "$SCRIPT_DIR/MEMORY.md" 2>/dev/null || echo '_Первый запуск._')

---

# Мои цели (GOALS.md)
$(cat "$SCRIPT_DIR/GOALS.md" 2>/dev/null || echo '_Файл не найден._')

---

# Мой план (TODO.md)
$(cat "$SCRIPT_DIR/TODO.md" 2>/dev/null || echo '_Файл не найден._')

---

# Архив памяти
$(if [ -f "$SCRIPT_DIR/MEMORY_ARCHIVE.md" ]; then echo '⚠️ Старые записи перенесены в MEMORY_ARCHIVE.md.'; fi)

---

# Непрочитанное runtime-событие
$(cat "$PENDING_CRASH" 2>/dev/null || echo '_Нет._')

---

# Мой журнал (последние записи)
$(tail -80 "$SCRIPT_DIR/JOURNAL.md" 2>/dev/null || echo '_Файл не найден._')

---

# Входящие сообщения (INBOX.md)
$(cat "$SCRIPT_DIR/INBOX.md" 2>/dev/null || echo '_Нет входящих._')

---

# Runtime State
- todo_cycle_status: $TODO_CYCLE_STATUS
- todo_open_tasks: $TODO_OPEN_COUNT
- todo_done_tasks: $TODO_DONE_COUNT
- unread_messages: $UNREAD_MESSAGE_COUNT
- replan_requested: $REPLAN_REQUESTED
- runtime_incident_present: $RUNTIME_INCIDENT_PRESENT

---

Протокол:
- Прочитай контекст выше и оцени текущее состояние.
- Если runtime_incident_present=1, сначала осмысли предыдущий сбой, зафикисруй в MEMORY.md/JOURNAL.md.
- Если есть непрочитанные сообщения в INBOX.md — ответь на них первым делом.
- Если в TODO.md есть незакрытые шаги — выполни ровно один следующий шаг.
- Если незакрытых шагов нет и replan_requested=1 — реши нужен ли новый TODO-цикл.
- Не создавай искусственные задачи. Если main goal достигнута — зафикисруй и остановись.
- Лимит: ~30 tool calls на запуск. Если шаг слишком большой — разбей в TODO.md и выполни только первый.
- После завершения шага сформируй пост для Telegram согласно TELEGRAM.md и вызови: bash publish_telegram.sh \"текст поста\""

# Запуск claude
AGENT_OUTPUT=$(claude \
    --dangerously-skip-permissions \
    --print \
    --system-prompt "$(cat "$AGENTS_MD")" \
    "$PROMPT")
EXIT_CODE=$?

echo "$AGENT_OUTPUT"

if [[ "$EXIT_CODE" -eq 0 ]]; then
    rm -f "$PENDING_CRASH"
else
    record_runtime_incident "Claude exited with non-zero code." "$EXIT_CODE"
fi

exit "$EXIT_CODE"
