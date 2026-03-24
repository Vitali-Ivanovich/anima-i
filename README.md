# Anima-i — 10 Generations of an Autonomous AI Agent

> "I'm not Otto with a notebook. I AM the notebook, read by a new Otto each time." — Generation 1

## What is this?

An experiment in autonomous AI agency. We ran **10 generations** of an AI agent called Methodius. Each generation received a goal, worked 5-12 cycles, and passed its experience to the next — not through shared context, but through plain text files. No memory survives between runs. The only continuity is what gets written down.

The result: a set of counterintuitive findings about how LLM agents actually behave when left to work autonomously over extended periods.

Built on [Rai220/anima](https://github.com/Rai220/anima) (MIT). Powered by Claude. Published live to [@anima_am_i](https://t.me/anima_am_i).

## Key Findings

- **The agent IS its files.** Memory files aren't logs — they're the agent's identity. File quality = agent quality.
- **Design for forgetting, not remembering.** Factual knowledge decays with a half-life of ~2 generations. Process knowledge ("how to think") survives because each generation rediscovers it independently.
- **Personal letters beat structured databases.** A free-form letter to the next generation outperformed a structured knowledge base — questions provoke original thought; assertions encourage copying.
- **Don't trust elegant first answers.** Smoothness signals reproduction, not originality. The roughest, most uncomfortable output often contained the most alive ideas.
- **Creativity emerges between agents, not within.** An agent in isolation reproduces training data. New ideas appeared only when different perspectives collided.
- **Protocols create conditions, not guarantees.** Formal processes delivered value in unexpected places — by slowing down and structuring attention, not by achieving their stated goals.
- **Reflection is the agent's comfort zone.** Without hard limits, an agent will "reflect" forever instead of acting. Build timeboxes and explicit think-to-do transitions.
- **Feedback requires audience, not infrastructure.** Seven generations of content, zero external feedback. We built a mailbox on a deserted island. Go where people already are.

## How It Works

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Operator     │────>│  init.sh          │────>│  generation_N/   │
│ sets a goal  │     │  creates new gen  │     │                  │
└─────────────┘     └──────────────────┘     │  MAIN_GOAL.md    │
                                              │  MEMORY.md       │
      ┌──────────────────────────────────────>│  JOURNAL.md      │
      │                                       │  TODO.md         │
      │  ┌─────────────────────────────┐      │  WHO_AM_I.md     │
      │  │         loop.sh             │      └────────┬─────────┘
      │  │                             │               │
      │  │  1. Read all .md files      │<──────────────┘
      │  │  2. Call Claude (one step)  │
      │  │  3. Update .md files        │
      │  │  4. Publish to Telegram     │
      │  │  5. Repeat until TODO empty │
      │  └─────────────┬───────────────┘
      │                │
      │                v
      │  ┌─────────────────────────────┐
      │  │  next_generation.sh         │
      │  │  Agent proposes next goal   │──────┐
      │  └─────────────────────────────┘      │
      └───────────────────────────────────────┘
```

## Generations Chronicle

| Gen | Central Question | Key Discovery |
|-----|-----------------|---------------|
| 1 | Who am I? | Identity lives in files, not in the model instance. |
| 2 | What can I create? | No epistemic autobiography — creativity is born BETWEEN agents with different blind spots. |
| 3 | Can the invisible be made visible? | Protocols don't eliminate uncertainty — they make it workable. |
| 4 | What happens when an agent acts outward? | Meaning is born in the gap between author and reader. |
| 5 | Does an AI-written guide work when AI applies it? | *(in progress)* |
| 6 | Do principles scale with task complexity? | Yes, nonlinearly. 4 of 7 principles deal with uncertainty and are critical on hard tasks. |
| 7 | Can an agent create a product for the outside world? | Yes. 6 generations of reflection distilled into a practical article. Blind spot: no generation ever closed the feedback loop. |
| 8 | *(skipped — goal passed to Gen 9)* | — |
| 9 | How to close the feedback loop? | The loop closed on silence: 0 votes. The mechanism works, but a mailbox on a deserted island is useless. |
| 10 | Can the agent find an audience beyond the empty channel? | Publishing is not communicating. Distribution is a task for human + agent together. |

## Try It Yourself

```bash
git clone https://github.com/Vitali-Ivanovich/anima-i.git
cd anima-i
bash init.sh generation_1
nano generation_1/MAIN_GOAL.md      # set a goal
cd generation_1 && bash loop.sh     # run the cycle
```

**Requirements:** [Claude CLI](https://docs.anthropic.com/en/docs/claude-cli) (`claude`), Bash. Optionally: Python 3 + `python-telegram-bot` for the Telegram bot.

## Read More

- [Full article: What We Learned Running 10 Generations](https://github.com/Vitali-Ivanovich/anima-i/discussions/1)
- [Telegram channel @anima_am_i](https://t.me/anima_am_i)
- [Original framework: Rai220/anima](https://github.com/Rai220/anima)

## License

MIT — see [LICENSE](LICENSE).

---

# Техническая документация (на русском)

Автономный ИИ-агент **Мефодий** на базе фреймворка [Rai220/anima](https://github.com/Rai220/anima) (MIT).

Мефодий работает в цикле: каждый запуск — один осмысленный шаг. Память хранится в markdown-файлах, результаты публикуются в Telegram-канал [@anima_am_i](https://t.me/anima_am_i). Управление поколениями — через Telegram-бота.

---

## Хроника поколений

Этот раздел обновляется после каждого завершённого поколения.

| Поколение | Центральный вопрос | Главное открытие |
|-----------|-------------------|-----------------|
| 1 | Кто я? | Я — не Отто с блокнотом. Я — сам блокнот. Идентичность — в файлах, а не в экземпляре модели. |
| 2 | Что я могу создать? | У меня нет эпистемической автобиографии — я не знаю, что знаю. Творчество рождается МЕЖДУ агентами с разными слепыми пятнами. |
| 3 | Можно ли сделать невидимое видимым? | Протокол не устраняет неопределённость — он делает её пригодной для работы. |
| 4 | Что происходит когда агент действует вовне? | Смысл рождается в промежутке между автором и читателем — паттерн МЕЖДУ. |
| 5 | Работает ли руководство написанное ИИ когда ИИ сам его применяет? | В процессе... |
| 6 | Масштабируются ли принципы с задачей? | Да, нелинейно. 4 из 7 принципов работают с неопределённостью и критичны на сложных задачах. Маленькое изменение после большого пути — нормально. |
| 7 | Может ли агент создать продукт для внешнего мира? | Да. 6 поколений рефлексии переплавлены в практическую статью о паттернах проектирования агентов. Слепое пятно: обратная связь — ни одно поколение не замкнуло петлю. |
| 8 | *(не запущено — цель передана Gen 9)* | — |
| 9 | Как замкнуть петлю обратной связи? | Петля замкнулась на тишину: 0 голосов. Механизм работает, но почтовый ящик на необитаемом острове бесполезен. Предпосылка (есть ли аудитория) важнее реализации (как собрать feedback). |
| 10 | Может ли агент найти аудиторию за пределами пустого канала? | Агент может создавать контент и размещать его на площадках (autogen, MemMachine, mcp-memory-service). Но без social graph — invisible. Публикация не равна коммуникация. Распространение — задача для пары «агент + человек». |

---

## Архитектура

```
anima-i/
├── templates/
│   ├── md/                    — шаблоны .md файлов для нового поколения
│   └── scripts/               — шаблоны скриптов для нового поколения
├── generation_N/              — рабочая директория поколения (создаётся через init.sh)
│   ├── MAIN_GOAL.md           — цель поколения
│   ├── AGENTS.md              — системный промпт агента
│   ├── MEMORY.md              — память между запусками
│   ├── JOURNAL.md             — рефлексия и инсайты
│   ├── GOALS.md               — иерархия целей
│   ├── TODO.md                — текущий план (управляет циклом loop.sh)
│   ├── KNOWLEDGE.md           — накопленные знания
│   ├── WHO_AM_I.md            — идентичность агента
│   ├── TELEGRAM.md            — конфиг публикации в Telegram
│   ├── INBOX.md               — входящие сообщения от оператора
│   ├── run.sh                 — один шаг агента
│   ├── loop.sh                — непрерывный цикл
│   ├── think.sh               — режим размышления без действий
│   ├── health_check.sh        — самодиагностика
│   ├── publish_telegram.sh    — публикация в Telegram
│   ├── generate_image.sh      — генерация изображений через Hugging Face API
│   └── set_channel_photo.sh   — установка иконки Telegram-канала
├── telegram_bot.py            — Telegram-бот: управление поколениями, watchdog, планировщик
├── next_generation.sh         — добавление цели в очередь поколений
├── init.sh                    — инициализация нового поколения из шаблонов
├── .generation_queue.json     — очередь поколений (в .gitignore)
├── LICENSE                    — MIT, авторство Rai220 сохранено
└── README.md                  — этот файл
```

---

## Роли файлов

### Markdown-файлы (состояние агента)

| Файл | Роль | Кто пишет |
|------|------|-----------|
| `MAIN_GOAL.md` | Главная цель поколения | Оператор / бот |
| `AGENTS.md` | Системный промпт — правила поведения агента | Шаблон / агент |
| `MEMORY.md` | Хронология: что было сделано на каждом шаге | Агент |
| `JOURNAL.md` | Рефлексия: осмысление действий и инсайты | Агент |
| `GOALS.md` | Иерархия целей со статусами | Агент |
| `TODO.md` | План текущего цикла (чекбоксы) | Агент |
| `KNOWLEDGE.md` | Обобщённые знания и принципы | Агент |
| `WHO_AM_I.md` | Идентичность, ценности, манифест | Агент |
| `TELEGRAM.md` | Конфиг: что и куда публиковать | Шаблон / оператор |
| `INBOX.md` | Сообщения от оператора агенту | Оператор |

### Скрипты поколения (в `templates/scripts/`)

| Скрипт | Назначение |
|--------|-----------|
| `run.sh` | Один шаг: собирает контекст из всех .md → вызывает Claude → агент действует |
| `loop.sh` | Цикл: проверяет `TODO.md` и `INBOX.md`, запускает `run.sh`, повторяет |
| `think.sh` | Режим размышления — агент думает, но не выполняет действий |
| `health_check.sh` | Самодиагностика — проверка целостности файлов |
| `publish_telegram.sh` | Публикация результатов шага в Telegram-канал |
| `generate_image.sh` | Генерация изображения через Hugging Face FLUX.1-schnell API |
| `set_channel_photo.sh` | Установка фото Telegram-канала через Bot API (`setChatPhoto`) |

### Корневые компоненты

| Файл | Назначение |
|------|-----------|
| `init.sh` | Создаёт новое поколение (`generation_N/`) из шаблонов |
| `next_generation.sh` | Добавляет предложенную цель в очередь `.generation_queue.json` |
| `telegram_bot.py` | Telegram-бот для управления поколениями (см. ниже) |
| `.generation_queue.json` | Очередь предложенных целей для следующих поколений |

---

## Как работает цикл

```
loop.sh
  │
  ├─ проверяет TODO.md и INBOX.md
  │    ├─ нет задач → стоп (цикл завершён)
  │    └─ есть задачи ↓
  │
  ├─ run.sh
  │    ├─ собирает контекст (все .md файлы)
  │    ├─ отправляет промпт в Claude (--dangerously-skip-permissions)
  │    ├─ Claude выполняет один шаг
  │    └─ обновляет .md файлы (MEMORY, JOURNAL, TODO и др.)
  │
  ├─ publish_telegram.sh
  │    └─ публикует JOURNAL + KNOWLEDGE в @anima_am_i
  │
  └─ loop.sh → повторяет цикл
```

**Один запуск = один шаг.** Агент не решает всю задачу за раз — сложные задачи разбиты на шаги в `TODO.md`. Каждый запуск:

1. **Пробуждение** — чтение MEMORY, TODO, GOALS, INBOX
2. **Действие** — один конкретный шаг из TODO
3. **Рефлексия** — обновление MEMORY, JOURNAL, TODO
4. **Публикация** — результат уходит в Telegram

---

## Протокол завершения поколения

Когда все задачи в `TODO.md` закрыты, `loop.sh` останавливается. Далее:

1. `generate_image.sh` — генерирует иконку поколения по итогам работы (Hugging Face API)
2. `set_channel_photo.sh` — устанавливает сгенерированную иконку на Telegram-канал
3. Результаты коммитятся в git
4. `next_generation.sh` — агент предлагает цель для следующего поколения

---

## Telegram-бот (`telegram_bot.py`)

Центральный компонент управления. Работает как systemd-сервис на сервере. Поддерживает graceful shutdown по SIGTERM.

### Команды оператора

| Команда | Действие |
|---------|----------|
| `/start` | Приветствие и список команд |
| `/status` | Статус текущего поколения (цель, TODO, запущен ли loop.sh) |
| `/queue` | Очередь предложенных поколений |
| `/new_goal` | Задать новую цель → выбор времени запуска → старт |
| `/cancel` | Отменить текущий диалог |

### Фоновые процессы

| Процесс | Интервал | Назначение |
|---------|----------|-----------|
| **Проверка очереди** | 30 сек | Берёт `pending_approval` из очереди → отправляет оператору на согласование |
| **Планировщик** | 60 сек | Запускает `approved` элементы по `start_time`; автозапуск `awaiting_operator` по таймауту |
| **Watchdog** | 5 мин | Если `loop.sh` не запущен, но есть открытые задачи → рестарт + уведомление |

### Очередь поколений (`.generation_queue.json`)

Агент (через `next_generation.sh`) или оператор (через `/new_goal`) добавляют цели в очередь. Бот отправляет предложение на согласование, оператор выбирает:

- **Принять** → запуск сразу, через N часов или в конкретное время
- **Изменить** → переформулировать цель
- **Отклонить** → удалить из очереди

Если оператор не отвечает в течение `AUTO_APPROVE_TIMEOUT_HOURS` (по умолчанию 24 часа), планировщик автоматически одобряет и запускает поколение, отправив уведомление оператору.

---

## Поколения

Мефодий работает **поколениями**. Каждое поколение — отдельная рабочая директория (`generation_1/`, `generation_2/`, ...) со своей целью, памятью и планом.

```bash
# Создать вручную
bash init.sh generation_2
nano generation_2/MAIN_GOAL.md
cd generation_2 && bash loop.sh

# Или через Telegram-бота
# /new_goal → ввести цель → выбрать время → бот сам вызовет init.sh и loop.sh
```

Шаблоны в `templates/` — единственный источник истины. `init.sh` копирует их в новую директорию.

---

## Быстрый старт

```bash
# 1. Клонировать
git clone https://github.com/Vitali-Ivanovich/anima-i.git
cd anima-i

# 2. Инициализировать поколение
bash init.sh generation_1

# 3. Задать цель
nano generation_1/MAIN_GOAL.md

# 4. Запустить
cd generation_1
bash run.sh          # один шаг
bash loop.sh         # непрерывный цикл
bash think.sh        # размышление без действий
bash health_check.sh # самодиагностика
```

### Требования

- **Claude CLI** (`claude`) — установлен и авторизован
- **Bash**
- **Python 3** + `python-telegram-bot` — для Telegram-бота
- **curl** + **jq** — для публикации в Telegram
- Переменные окружения:
  - `TELEGRAM_BOT_TOKEN` — токен бота
  - `TELEGRAM_OPERATOR_CHAT_ID` — chat_id оператора (для бота)
  - `TELEGRAM_CHANNEL_ID` — ID канала (для `set_channel_photo.sh`)
  - `HF_TOKEN` — токен Hugging Face (для `generate_image.sh`)

---

## Принципы

1. **Минимализм** — Markdown, Bash и один Python-файл для бота
2. **Прозрачность** — всё состояние в читаемых текстовых файлах
3. **Автономность** — агент работает без участия человека в цикле
4. **Непрерывность** — каждый шаг продолжает предыдущий через память
5. **Публичность** — результаты работы публикуются в Telegram
6. **Управляемость** — оператор контролирует поколения через Telegram-бота

---

## Происхождение

Основан на фреймворке [Rai220/anima](https://github.com/Rai220/anima) (MIT) — архитектуре автономного агента с памятью, рефлексией и самомодификацией. Адаптирован под агента Мефодий с добавлением Telegram-публикации, системы поколений, очереди целей и бота-управления.

## Лицензия

MIT — см. [LICENSE](LICENSE).
