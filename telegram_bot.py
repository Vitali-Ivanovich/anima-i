#!/usr/bin/env python3
"""
telegram_bot.py — Telegram-бот для управления поколениями Мефодия.

Функции:
- Слушает очередь поколений (.generation_queue.json)
- Отправляет оператору предложения на согласование
- Запускает новое поколение по команде или в назначенное время
- Позволяет оператору добавить свою цель в очередь

Переменные окружения:
- TELEGRAM_BOT_TOKEN — токен бота
- TELEGRAM_OPERATOR_CHAT_ID — chat_id оператора
- ANIMA_PROJECT_DIR — путь к корню проекта (по умолчанию ~/anima-i)
"""

import os
import json
import signal
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)
from telegram.request import HTTPXRequest

# Настройка логирования — без токена в выводе
logging.basicConfig(
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("/tmp/mefodiy_bot.log"),
        logging.StreamHandler()
    ]
)
# Подавляем httpx логи чтобы токен не светился
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Конфигурация из окружения
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
OPERATOR_CHAT_ID = int(os.environ["TELEGRAM_OPERATOR_CHAT_ID"])
PROJECT_DIR = Path(os.environ.get("ANIMA_PROJECT_DIR", Path.home() / "anima-i"))
QUEUE_FILE = PROJECT_DIR / ".generation_queue.json"

# Интервал проверки очереди (секунды)
QUEUE_CHECK_INTERVAL = 30

# Таймаут автозапуска: если оператор не ответил на предложение — запустить автоматически
AUTO_APPROVE_TIMEOUT_HOURS = 24

# Состояния диалога
AWAIT_GOAL, AWAIT_TIME, AWAIT_TIME_VALUE, AWAIT_CONFIRM = range(4)


# --- Утилиты очереди ---

def read_queue() -> dict:
    """Читает очередь поколений."""
    if not QUEUE_FILE.exists():
        return {"queue": []}
    try:
        with open(QUEUE_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка чтения очереди: {e}")
        return {"queue": []}


def write_queue(data: dict):
    """Записывает очередь поколений."""
    with open(QUEUE_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_pending_item() -> dict | None:
    """Возвращает первый элемент очереди со статусом pending_approval."""
    data = read_queue()
    for item in data["queue"]:
        if item["status"] == "pending_approval":
            return item
    return None


def update_item_status(proposed_at: str, status: str, start_time: str = None):
    """Обновляет статус элемента очереди."""
    data = read_queue()
    for item in data["queue"]:
        if item["proposed_at"] == proposed_at:
            item["status"] = status
            if start_time:
                item["start_time"] = start_time
            break
    write_queue(data)


def remove_item(proposed_at: str):
    """Удаляет элемент из очереди."""
    data = read_queue()
    data["queue"] = [i for i in data["queue"] if i["proposed_at"] != proposed_at]
    write_queue(data)


def get_next_generation_num() -> int:
    """Определяет номер следующего поколения."""
    existing = sorted(PROJECT_DIR.glob("generation_*/"))
    if not existing:
        return 1
    last = existing[-1].name.replace("generation_", "")
    try:
        return int(last) + 1
    except ValueError:
        return len(existing) + 1


def get_current_generation_dir() -> Path | None:
    """Возвращает директорию текущего поколения."""
    existing = sorted(PROJECT_DIR.glob("generation_*/"))
    return existing[-1] if existing else None


async def is_generation_running() -> bool:
    """Проверяет запущен ли сейчас loop.sh (неблокирующий)."""
    proc = await asyncio.create_subprocess_exec(
        "pgrep", "-f", "loop.sh",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
    returncode = await proc.wait()
    return returncode == 0


# --- Запуск поколения ---

async def start_generation(goal: str, generation_num: int, app: Application):
    """Инициализирует и запускает новое поколение (неблокирующий)."""
    gen_dir = PROJECT_DIR / f"generation_{generation_num}"
    logger.info(f"Запуск поколения {generation_num}")

    # Инициализация через init.sh (неблокирующий)
    proc = await asyncio.create_subprocess_exec(
        "bash", str(PROJECT_DIR / "init.sh"), str(gen_dir),
        cwd=str(PROJECT_DIR),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        logger.error(f"init.sh завершился с ошибкой: {stderr.decode()}")
        return

    # Записываем цель
    (gen_dir / "MAIN_GOAL.md").write_text(f"# Main Goal\n\n{goal}\n")

    # Запускаем loop.sh в фоне (detached — не ждём завершения)
    log_file = gen_dir / ".runtime" / "loop.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    with open(log_file, "w") as lf:
        await asyncio.create_subprocess_exec(
            "bash", "loop.sh",
            cwd=str(gen_dir),
            stdout=lf,
            stderr=asyncio.subprocess.STDOUT,
            start_new_session=True
        )

    logger.info(f"Поколение {generation_num} запущено")
    await app.bot.send_message(
        chat_id=OPERATOR_CHAT_ID,
        text=f"🚀 *Поколение {generation_num} запущено*\n\nЦель: _{goal[:300]}_",
        parse_mode="Markdown"
    )


# --- Фоновые задачи (callbacks для job_queue) ---

async def check_queue(context: ContextTypes.DEFAULT_TYPE):
    """Проверяет очередь и инициирует согласование."""
    try:
        item = get_pending_item()
        if item:
            source_label = "Мефодий" if item["source"] == "mefodiy" else "Оператор"
            gen_num = get_next_generation_num()

            keyboard = [["✅ Принять", "✏️ Изменить", "❌ Отклонить"]]
            markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

            # Помечаем как отправленное чтобы не слать повторно
            update_item_status(item["proposed_at"], "awaiting_operator")

            await context.bot.send_message(
                chat_id=OPERATOR_CHAT_ID,
                text=(
                    f"🧠 *Предложение от {source_label}*\n\n"
                    f"Цель поколения {gen_num}:\n\n"
                    f"_{item['goal'][:500]}_\n\n"
                    f"Принять, изменить или отклонить?"
                ),
                parse_mode="Markdown",
                reply_markup=markup
            )
    except Exception as e:
        logger.error(f"Ошибка проверки очереди: {e}")


# --- Обработчики команд ---

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствие."""
    if update.effective_chat.id != OPERATOR_CHAT_ID:
        return
    await update.message.reply_text(
        "👋 Привет, Виталий!\n\n"
        "Команды:\n"
        "/status — статус текущего поколения\n"
        "/new_goal — задать новую цель\n"
        "/queue — очередь поколений\n"
        "/cancel — отменить текущее действие"
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает статус текущего поколения."""
    if update.effective_chat.id != OPERATOR_CHAT_ID:
        return

    gen_dir = get_current_generation_dir()
    if not gen_dir:
        await update.message.reply_text("Поколений пока нет.")
        return

    gen_num = gen_dir.name.replace("generation_", "")
    goal_text = (gen_dir / "MAIN_GOAL.md").read_text() if (gen_dir / "MAIN_GOAL.md").exists() else ""
    goal = goal_text.replace("# Main Goal", "").strip()

    todo_text = (gen_dir / "TODO.md").read_text() if (gen_dir / "TODO.md").exists() else ""
    open_tasks = todo_text.count("- [ ]")
    done_tasks = todo_text.count("- [x]")

    running = "🟢 запущено" if await is_generation_running() else "🔴 остановлено"

    await update.message.reply_text(
        f"📊 *Поколение {gen_num}* — {running}\n\n"
        f"Цель: _{goal[:300]}_\n\n"
        f"TODO: {done_tasks} выполнено / {open_tasks} открыто",
        parse_mode="Markdown"
    )


async def cmd_queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает очередь поколений."""
    if update.effective_chat.id != OPERATOR_CHAT_ID:
        return

    data = read_queue()
    if not data["queue"]:
        await update.message.reply_text("Очередь пуста.")
        return

    text = "📋 *Очередь поколений:*\n\n"
    for i, item in enumerate(data["queue"], 1):
        source = "Мефодий" if item["source"] == "mefodiy" else "Оператор"
        status_map = {
            "pending_approval": "⏳ ожидает согласования",
            "awaiting_operator": "📨 отправлено оператору",
            "approved": "✅ одобрено",
            "scheduled": f"⏰ запланировано на {item.get('start_time', '?')}",
        }
        status = status_map.get(item["status"], item["status"])
        text += f"{i}. _{item['goal'][:150]}_\n   {source} · {status}\n\n"

    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_new_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Оператор задаёт новую цель."""
    if update.effective_chat.id != OPERATOR_CHAT_ID:
        return
    await update.message.reply_text(
        "Введи цель для следующего поколения:",
        reply_markup=ReplyKeyboardRemove()
    )
    return AWAIT_GOAL


async def receive_new_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает цель от оператора."""
    if update.effective_chat.id != OPERATOR_CHAT_ID:
        return

    goal = update.message.text
    context.user_data["pending_goal"] = goal
    context.user_data["pending_source"] = "operator"

    keyboard = [["▶️ Сразу", "⏰ Через N часов", "📅 В конкретное время"]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        f"Цель:\n_{goal[:300]}_\n\nКогда запустить?",
        parse_mode="Markdown",
        reply_markup=markup
    )
    return AWAIT_TIME


async def receive_time_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор времени запуска."""
    if update.effective_chat.id != OPERATOR_CHAT_ID:
        return

    text = update.message.text

    if text == "▶️ Сразу":
        context.user_data["start_time"] = None
        return await confirm_and_queue(update, context)

    elif text == "⏰ Через N часов":
        await update.message.reply_text(
            "Через сколько часов запустить? (введи число)",
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data["time_mode"] = "hours"
        return AWAIT_TIME_VALUE

    elif text == "📅 В конкретное время":
        await update.message.reply_text(
            "Введи время в формате `2026-03-22 14:00`",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data["time_mode"] = "absolute"
        return AWAIT_TIME_VALUE


async def receive_time_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает конкретное значение времени."""
    if update.effective_chat.id != OPERATOR_CHAT_ID:
        return

    text = update.message.text
    mode = context.user_data.get("time_mode")

    if mode == "hours":
        try:
            hours = float(text)
            start_time = (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M")
            context.user_data["start_time"] = start_time
        except ValueError:
            await update.message.reply_text("Введи число, например: 2")
            return AWAIT_TIME_VALUE
    else:
        context.user_data["start_time"] = text

    return await confirm_and_queue(update, context)


async def confirm_and_queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждает и добавляет в очередь."""
    goal = context.user_data["pending_goal"]
    source = context.user_data.get("pending_source", "operator")
    start_time = context.user_data.get("start_time")

    # Добавляем в очередь
    data = read_queue()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data["queue"].append({
        "goal": goal,
        "source": source,
        "status": "approved" if start_time else "approved",
        "start_time": start_time,
        "proposed_at": timestamp
    })
    write_queue(data)

    time_label = f"в {start_time}" if start_time else "сразу"
    await update.message.reply_text(
        f"✅ Добавлено в очередь\n\nЗапуск: {time_label}",
        reply_markup=ReplyKeyboardRemove()
    )

    # Если сразу — запускаем
    if not start_time:
        gen_num = get_next_generation_num()
        remove_item(timestamp)
        await start_generation(goal, gen_num, context.application)

    return ConversationHandler.END


async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ответ оператора на предложение из очереди."""
    if update.effective_chat.id != OPERATOR_CHAT_ID:
        return

    text = update.message.text
    data = read_queue()

    # Находим элемент ожидающий ответа оператора
    awaiting = next(
        (i for i in data["queue"] if i["status"] == "awaiting_operator"),
        None
    )

    if not awaiting:
        return

    if text == "✅ Принять":
        keyboard = [["▶️ Сразу", "⏰ Через N часов", "📅 В конкретное время"]]
        markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        context.user_data["pending_goal"] = awaiting["goal"]
        context.user_data["pending_source"] = awaiting["source"]
        context.user_data["pending_proposed_at"] = awaiting["proposed_at"]
        remove_item(awaiting["proposed_at"])
        await update.message.reply_text("Когда запустить?", reply_markup=markup)
        return AWAIT_TIME

    elif text == "✏️ Изменить":
        context.user_data["pending_proposed_at"] = awaiting["proposed_at"]
        remove_item(awaiting["proposed_at"])
        await update.message.reply_text(
            f"Текущая цель:\n_{awaiting['goal'][:300]}_\n\nВведи новую формулировку:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        return AWAIT_GOAL

    elif text == "❌ Отклонить":
        remove_item(awaiting["proposed_at"])
        await update.message.reply_text(
            "Цель отклонена.",
            reply_markup=ReplyKeyboardRemove()
        )


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет текущий диалог."""
    await update.message.reply_text("Отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def watchdog(context: ContextTypes.DEFAULT_TYPE):
    """
    Проверяет не завис ли текущий цикл агента.
    Если loop.sh не запущен а поколение не завершено — рестартует.
    """
    try:
        gen_dir = get_current_generation_dir()
        if not gen_dir:
            return

        if await is_generation_running():
            return

        # Проверяем есть ли незакрытые задачи
        todo_text = (gen_dir / "TODO.md").read_text() if (gen_dir / "TODO.md").exists() else ""
        open_tasks = todo_text.count("- [ ]")

        if open_tasks > 0:
            logger.warning("Watchdog: loop.sh не запущен, есть открытые задачи — рестарт")
            log_file = gen_dir / ".runtime" / "loop.log"
            log_file.parent.mkdir(parents=True, exist_ok=True)

            with open(log_file, "a") as lf:
                await asyncio.create_subprocess_exec(
                    "bash", "loop.sh",
                    cwd=str(gen_dir),
                    stdout=lf,
                    stderr=asyncio.subprocess.STDOUT,
                    start_new_session=True
                )

            await context.bot.send_message(
                chat_id=OPERATOR_CHAT_ID,
                text="⚠️ Watchdog: Мефодий завис, перезапустил цикл."
            )
    except Exception as e:
        logger.error(f"Watchdog ошибка: {e}")


# --- Планировщик запусков ---

async def scheduler(context: ContextTypes.DEFAULT_TYPE):
    """Проверяет запланированные запуски и стартует их вовремя.
    Также автоматически одобряет элементы awaiting_operator по таймауту."""
    try:
        data = read_queue()
        now = datetime.now()

        for item in data["queue"]:
            # Запланированные запуски — по времени
            if item["status"] == "approved" and item.get("start_time"):
                try:
                    start_dt = datetime.strptime(item["start_time"], "%Y-%m-%d %H:%M")
                    if now >= start_dt:
                        gen_num = get_next_generation_num()
                        remove_item(item["proposed_at"])
                        await start_generation(item["goal"], gen_num, context.application)
                        logger.info(f"Планировщик запустил поколение {gen_num}")
                except ValueError:
                    pass

            # Автозапуск по таймауту — оператор не ответил
            if item["status"] == "awaiting_operator":
                try:
                    proposed_dt = datetime.strptime(item["proposed_at"], "%Y-%m-%d %H:%M:%S")
                    elapsed = now - proposed_dt
                    if elapsed >= timedelta(hours=AUTO_APPROVE_TIMEOUT_HOURS):
                        gen_num = get_next_generation_num()
                        logger.info(
                            f"Автозапуск по таймауту ({AUTO_APPROVE_TIMEOUT_HOURS}ч): "
                            f"поколение {gen_num}"
                        )
                        await context.bot.send_message(
                            chat_id=OPERATOR_CHAT_ID,
                            text=(
                                f"⏰ {AUTO_APPROVE_TIMEOUT_HOURS} часов без ответа — "
                                f"запускаю поколение {gen_num} автоматически"
                            ),
                            reply_markup=ReplyKeyboardRemove()
                        )
                        remove_item(item["proposed_at"])
                        await start_generation(item["goal"], gen_num, context.application)
                except ValueError:
                    pass
    except Exception as e:
        logger.error(f"Планировщик ошибка: {e}")


async def post_init(app: Application):
    """Регистрация фоновых задач после инициализации приложения."""
    app.job_queue.run_repeating(check_queue, interval=QUEUE_CHECK_INTERVAL, first=10)
    app.job_queue.run_repeating(scheduler, interval=60, first=15)
    app.job_queue.run_repeating(watchdog, interval=300, first=30)
    logger.info("Фоновые задачи зарегистрированы")


async def post_shutdown(app: Application):
    """Cleanup при остановке."""
    logger.info("Бот остановлен")


def main():
    request = HTTPXRequest(read_timeout=30, connect_timeout=30, write_timeout=30)
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .request(request)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("new_goal", cmd_new_goal),
            MessageHandler(
                filters.TEXT & filters.Regex("^(✅ Принять|✏️ Изменить|❌ Отклонить)$"),
                handle_approval
            )
        ],
        states={
            AWAIT_GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_new_goal)],
            AWAIT_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_time_choice)],
            AWAIT_TIME_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_time_value)],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("queue", cmd_queue))

    # Graceful shutdown по SIGTERM (systemd)
    def handle_sigterm(signum, frame):
        logger.info("Получен SIGTERM, останавливаюсь...")
        # run_polling слушает asyncio signals, но SIGTERM нужно пробросить
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, handle_sigterm)

    logger.info("Мефодий-бот запущен. Слушаю оператора...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
