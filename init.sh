#!/bin/bash
# init.sh — Инициализация нового поколения агента Мефодий
# Использование: bash init.sh <директория>
# Копирует шаблоны из templates/md/ и скрипты из templates/scripts/

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATES_MD="$SCRIPT_DIR/templates/md"
TEMPLATES_SCRIPTS="$SCRIPT_DIR/templates/scripts"
TARGET_DIR="${1:-.}"

mkdir -p "$TARGET_DIR"

echo "🤖 Инициализация агента Мефодий"
echo "   Директория: $(cd "$TARGET_DIR" && pwd)"
echo ""

# Копируем .md шаблоны (не перезаписываем существующие)
TEMPLATE_FILES=("MEMORY.md" "TODO.md" "GOALS.md" "JOURNAL.md" "KNOWLEDGE.md" "WHO_AM_I.md" "MAIN_GOAL.md" "AGENTS.md" "TELEGRAM.md")
for f in "${TEMPLATE_FILES[@]}"; do
    if [[ -f "$TARGET_DIR/$f" ]]; then
        echo "  ⏭  $f — уже существует, пропускаю"
    elif [[ -f "$TEMPLATES_MD/$f" ]]; then
        cp "$TEMPLATES_MD/$f" "$TARGET_DIR/$f"
        echo "  ✅ $f — создан из шаблона"
    else
        echo "  ❌ $f — шаблон не найден в $TEMPLATES_MD"
    fi
done

# Копируем скрипты
SCRIPT_FILES=("run.sh" "think.sh" "loop.sh" "health_check.sh" "publish_telegram.sh" "generate_image.sh" "set_channel_photo.sh")
for f in "${SCRIPT_FILES[@]}"; do
    if [[ -f "$TARGET_DIR/$f" ]]; then
        echo "  ⏭  $f — уже существует, пропускаю"
    elif [[ -f "$TEMPLATES_SCRIPTS/$f" ]]; then
        cp "$TEMPLATES_SCRIPTS/$f" "$TARGET_DIR/$f"
        chmod +x "$TARGET_DIR/$f"
        echo "  ✅ $f — скопирован"
    else
        echo "  ❌ $f — не найден в $TEMPLATES_SCRIPTS"
    fi
done

echo ""
echo "🎉 Готово! Следующие шаги:"
echo ""
echo "  1. Отредактируйте MAIN_GOAL.md — опишите задачу для агента"
echo "  2. Настройте TELEGRAM.md — параметры публикации"
echo "  3. Запустите агента:"
echo "     bash run.sh             — один шаг"
echo "     bash loop.sh            — непрерывный цикл"
echo "     bash think.sh           — режим размышления"
echo "     bash health_check.sh    — самодиагностика"
echo ""
