#!/usr/bin/env python3
"""
telegram_bot.py — Telegram-бот для управления поколениями Мефодия.

Функции:
- Получает сообщения от оператора (согласование цели и времени запуска)
- Запускает новое поколение по команде или в назначенное время
- Позволяет оператору задать свою цель и время старта

Переменные окружения:
- TELEGRAM_BOT_TOKEN — токен бота
- TELEGRAM_OPERATOR_CHAT_ID — chat_id оператора (Виталий)
- ANIMA_PROJECT_DIR — путь к корню проекта (по умолчанию ~/anima-i)
"""

import os
import asyncio
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("/tmp/mefodiy_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Конфигурация из окружения
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
OPERATOR_CHAT_ID = int(os.environ["TELEGRAM_OPERATOR_CHAT_ID"])
PROJECT_DIR = Path(os.environ.get("ANIMA_PROJECT_DIR", Path.home() / "anima-i"))

# Состояния диалога согласования
AWAIT_GOAL_CONFIRM, AWAIT_TIME, AWAIT_TIME_CONFIRM = range(3)

# Хранилище pending-предложений от Мефодия
pending = {
    "goal": None,
    "start_time": None,
    "generation_num": None,
}


def is_operator(update: Update) -> bool:
    """Проверяет что сообщение от оператора."""
    return update.effective_chat.id == OPERATOR_CHAT_ID


def get_next_generation_num() -> int:
    """Определяет номер следующего поколения по существующим директориям."""
    existing = sorted(PROJECT_DIR.glob("generation_*/"))
    if not existing:
        return 1
    last = existing[-1].name.replace("generation_", "")
    try:
        return int(last) + 1
    except ValueError:
        return len(existing) + 1


def get_current_generation_dir() -> Path:
    """Возвращает директорию текущего (последнего) поколения."""
    existing = sorted(PROJECT_DIR.glob("generation_*/"))
    if not existing:
        return None
    return existing[-1]


async def start_generation(goal: str, generation_num: int):
    """Инициализирует и запускает новое поколение в фоне."""
    gen_dir = PROJECT_DIR / f"generation_{generation_num}"
    logger.info(f"Запуск поколения {generation_num} в {gen_dir}")

    # Инициализация через init.sh
    subprocess.run(
        ["bash", str(PROJECT_DIR / "init.sh"), str(gen_dir)],
        cwd=str(PROJECT_DIR)
    )

    # Записываем цель
    (gen_dir / "MAIN_GOAL.md").write_text(f"# Main Goal\n\n{goal}\n")

    # Запускаем loop.sh в фоне через nohup
    log_file = gen_dir / ".runtime" / "loop.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    subprocess.Popen(
        ["bash", "loop.sh"],
        cwd=str(gen_dir),
        stdout=open(log_file, "w"),
        stderr=subprocess.STDOUT,
        start_new_session=True
    )
    logger.info(f"Поколение {generation_num} запущено, лог: {log_file}")


async def propose_next_generation(app: Application, goal: str):
    """Мефодий предлагает цель следующего поколения оператору."""
    gen_num = get_next_generation_num()
    pending["goal"] = goal
    pending["generation_num"] = gen_num

    keyboard = [["✅ Принять цель", "✏️ Изменить цель"]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await app.bot.send_message(
        chat_id=OPERATOR_CHAT_ID,
        text=(
            f"🧠 *Мефодий завершил поколение {gen_num - 1}*\n\n"
            f"Предлагаю цель для поколения {gen_num}:\n\n"
            f"_{goal}_\n\n"
            f"Принять или изменить?"
        ),
        parse_mode="Markdown",
        reply_markup=markup
    )


# --- Обработчики команд ---

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает статус текущего поколения."""
    if not is_operator(update):
        return

    gen_dir = get_current_generation_dir()
    if not gen_dir:
        await update.message.reply_text("Поколений пока нет.")
        return

    gen_num = gen_dir.name.replace("generation_", "")
    goal = (gen_dir / "MAIN_GOAL.md").read_text().strip().replace("# Main Goal", "").strip() if (gen_dir / "MAIN_GOAL.md").exists() else "нет"

    # Считаем открытые и закрытые задачи
    todo_text = (gen_dir / "TODO.md").read_text() if (gen_dir / "TODO.md").exists() else ""
    open_tasks = todo_text.count("- [ ]")
    done_tasks = todo_text.count("- [x]")

    await update.message.reply_text(
        f"📊 *Поколение {gen_num}*\n\n"
        f"Цель: _{goal[:200]}_\n\n"
        f"TODO: {done_tasks} выполнено / {open_tasks} открыто",
        parse_mode="Markdown"
    )


async def cmd_new_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Оператор задаёт новую цель вручную."""
    if not is_operator(update):
        return

    await update.message.reply_text(
        "Введи новую цель для следующего поколения:"
    )
    return AWAIT_GOAL_CONFIRM


async def receive_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает цель от оператора и спрашивает время запуска."""
    if not is_operator(update):
        return

    goal = update.message.text
    context.user_data["new_goal"] = goal
    pending["goal"] = goal
    pending["generation_num"] = get_next_generation_num()

    keyboard = [["▶️ Сразу", "⏰ Указать время"]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        f"Цель принята:\n_{goal}_\n\nКогда запустить?",
        parse_mode="Markdown",
        reply_markup=markup
    )
    return AWAIT_TIME


async def receive_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает время запуска и подтверждает."""
    if not is_operator(update):
        return

    text = update.message.text

    if text == "▶️ Сразу":
        pending["start_time"] = None
        gen_num = pending["generation_num"]
        goal = pending["goal"]

        await update.message.reply_text(
            f"🚀 Запускаю поколение {gen_num}..."
        )
        await start_generation(goal, gen_num)
        await update.message.reply_text(
            f"✅ Поколение {gen_num} запущено."
        )
        return ConversationHandler.END

    elif text == "⏰ Указать время":
        await update.message.reply_text(
            "Введи время запуска в формате:\n"
            "`через 2 часа` или `завтра в 9:00` или `2026-03-22 09:00`",
            parse_mode="Markdown"
        )
        return AWAIT_TIME_CONFIRM

    else:
        # Пробуем распарсить время
        context.user_data["start_time_raw"] = text
        pending["start_time"] = text

        await update.message.reply_text(
            f"Запланировать поколение {pending['generation_num']} на: *{text}*?",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(
                [["✅ Да", "❌ Отмена"]],
                one_time_keyboard=True, resize_keyboard=True
            )
        )
        return AWAIT_TIME_CONFIRM


async def confirm_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждает запланированный запуск."""
    if not is_operator(update):
        return

    text = update.message.text

    if text == "✅ Да":
        gen_num = pending["generation_num"]
        goal = pending["goal"]
        start_time_raw = pending["start_time"]

        # Простой парсинг "через N часов"
        delay_seconds = None
        if "через" in start_time_raw and "час" in start_time_raw:
            import re
            match = re.search(r"через\s+(\d+)\s+час", start_time_raw)
            if match:
                delay_seconds = int(match.group(1)) * 3600
        elif "через" in start_time_raw and "мин" in start_time_raw:
            import re
            match = re.search(r"через\s+(\d+)\s+мин", start_time_raw)
            if match:
                delay_seconds = int(match.group(1)) * 60

        if delay_seconds:
            await update.message.reply_text(
                f"⏰ Поколение {gen_num} запустится через {start_time_raw}."
            )
            await asyncio.sleep(delay_seconds)
            await start_generation(goal, gen_num)
            await update.message.reply_text(f"🚀 Поколение {gen_num} запущено!")
        else:
            await update.message.reply_text(
                f"⏰ Время '{start_time_raw}' принято. Запускаю сразу (планировщик в разработке)."
            )
            await start_generation(goal, gen_num)

        return ConversationHandler.END

    else:
        await update.message.reply_text("Отменено.")
        return ConversationHandler.END


async def handle_confirm_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Оператор подтверждает или отклоняет предложенную Мефодием цель."""
    if not is_operator(update):
        return

    text = update.message.text

    if text == "✅ Принять цель":
        keyboard = [["▶️ Сразу", "⏰ Указать время"]]
        markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            "Цель принята. Когда запустить?",
            reply_markup=markup
        )
        return AWAIT_TIME

    elif text == "✏️ Изменить цель":
        await update.message.reply_text("Введи новую формулировку цели:")
        return AWAIT_GOAL_CONFIRM

    else:
        context.user_data["new_goal"] = text
        pending["goal"] = text
        keyboard = [["▶️ Сразу", "⏰ Указать время"]]
        markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            f"Цель обновлена:\n_{text}_\n\nКогда запустить?",
            parse_mode="Markdown",
            reply_markup=markup
        )
        return AWAIT_TIME


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет текущий диалог."""
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Conversation handler для согласования цели и времени
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("new_goal", cmd_new_goal),
            MessageHandler(
                filters.TEXT & filters.Regex("^(✅ Принять цель|✏️ Изменить цель)$"),
                handle_confirm_goal
            )
        ],
        states={
            AWAIT_GOAL_CONFIRM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_goal)
            ],
            AWAIT_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_time)
            ],
            AWAIT_TIME_CONFIRM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_time)
            ],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("status", cmd_status))

    logger.info("Мефодий-бот запущен. Слушаю оператора...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
