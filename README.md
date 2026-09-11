# ⚡ TeleLang — Полная документация языка и CLI

**TeleLang** — предметно-ориентированный язык программирования (DSL) для разработки полнофункциональных Telegram-ботов (на базе `aiogram 3.x`) и юзерботов (на базе `Telethon` MTProto).

Код на TeleLang компилируется в чистый, идиоматичный и асинхронный Python. Вам не нужно вручную регистрировать роутеры, настраивать диспетчеры, FSM и зависимости — всё компилируется и работает автоматически.

---

## 📑 Оглавление

1. [Быстрый старт за 1 минуту](#1-быстрый-старт-за-1-минуту)
2. [CLI утилита tele (Все команды консоли)](#2-cli-утилита-tele-все-команды-консоли)
3. [Структура файлов и точки входа](#3-структура-файлов-и-точки-входа)
4. [Декларации верхнего уровня](#4-декларации-верхнего-уровня)
   - [`token`](#token)
   - [`bot`](#bot)
   - [`userbot`](#userbot)
   - [`command`](#command)
   - [`on message`](#on-message)
   - [`function`](#function)
   - [`database`](#database)
   - [`state`](#state)
   - [`roles`](#roles)
   - [`api`](#api)
   - [`ai`](#ai)
   - [`every` (планировщик)](#every-планировщик)
   - [`antispam`](#antispam)
   - [`locales`](#locales)
   - [`inline_query`](#inline_query)
   - [`import`](#import)
5. [События и Хуки (Middlewares)](#5-события-и-хуки-middlewares)
   - [`before_command` и `after_command`](#before_command-и-after_command)
   - [`on_error`](#on_error)
   - [`on_member_join` и `on_member_leave`](#on_member_join-и-on_member_leave)
   - [`on_payment`](#on_payment)
   - [`on_join_request`](#on_join_request)
   - [`on_poll_answer`](#on_poll_answer)
   - [`on_checklist_task_done`](#on_checklist_task_done)
6. [Инструкции и действия (Statements)](#6-инструкции-и-действия-statements)
   - [`send`, `send photo`, `video_note`, `document`](#send-send-photo-video_note-document)
   - [`send to`](#send-to)
   - [`broadcast`](#broadcast)
   - [`buttons` (Inline кнопки и URL)](#buttons-inline-кнопки-и-url)
   - [`ask` и `save`](#ask-и-save)
   - [`react` и `remove reaction`](#react-и-remove-reaction)
   - [`send poll` и `send quiz`](#send-poll-и-send-quiz)
   - [`send checklist`](#send-checklist)
   - [`send rich`](#send-rich)
   - [`send_invoice`](#send_invoice)
   - [`stream reply from ai`](#stream-reply-from-ai)
   - [`let`, `if / else`, присваивания и операции](#let-if--else-присваивания-и-операции)
   - [`log`](#log)
7. [Контекстные переменные и операторы](#7-контекстные-переменные-и-операторы)
8. [Docker & Деплой (`tele docker`)](#8-docker--деплой-tele-docker)
9. [Сборка в чистый Python (`tele build`)](#9-сборка-в-чистый-python-tele-build)
10. [Локальное тестирование без сети (`tele test`)](#10-локальное-тестирование-без-сети-tele-test)

---

## 1. Быстрый старт за 1 минуту

### Установка:
```bash
git clone https://github.com/tapochiek/telelang.git
cd telelang
pip install -e .
```

### Первый бот (`bot.tl`):
```telelang
token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
bot "MyFirstBot"

command "/start" {
    send "Привет, {user.name}! Добро пожаловать в TeleLang."
    buttons {
        "🚀 Узнать больше" -> show_info()
        "🌐 Официальный сайт" -> url("https://telegram.org")
    }
}

function show_info() {
    send "TeleLang компилирует простой код в чистый aiogram 3!"
}
```

### Запуск:
```bash
tele dev bot.tl
```

---

## 2. CLI утилита `tele` (Все команды консоли)

| Команда | Описание | Примеры вызова |
| :--- | :--- | :--- |
| **`tele dev`** | Запуск в режиме разработки с **авто-перезагрузкой (hot-reload)** при изменении файлов | `tele dev bot.tl`<br>`tele dev .`<br>`tele dev ./mybot` |
| **`tele run`** | Запуск бота в боевом режиме (production) | `tele run bot.tl`<br>`tele run .` |
| **`tele build`** | Сборка в автономный чистый Python-проект (`<имя>_py/`) или отдельный файл | `tele build mybot/`<br>`tele build bot.tl`<br>`tele build bot.tl -o bot.py` |
| **`tele docker`** | Генерация готовых **`Dockerfile`**, **`docker-compose.yml`** и **`.dockerignore`** под проект | `tele docker .`<br>`tele docker mybot/` |
| **`tele test`** | **Локальный интерактивный эмулятор** в терминале без интернета и подключения к Telegram | `tele test bot.tl`<br>`tele test .` |
| **`tele check`** | Проверка синтаксиса, типов и отсутствия циклических импортов | `tele check bot.tl`<br>`tele check .` |
| **`tele stats`** | Просмотр статистики зарегистрированных пользователей и состояния SQLite базы данных | `tele stats bot.tl`<br>`tele stats .` |
| **`tele init`** | Генерация структуры нового модульного проекта | `tele init my_bot` |
| **`tele format`** | Автоматическое форматирование кода `.tl` | `tele format bot.tl` |

---

## 3. Структура файлов и точки входа

TeleLang поддерживает как одиночные файлы (`bot.tl`), так и полноценные архитектуры проектов:
```
mybot/
├── main.tl              # Главная точка входа (токен, бот, импорты)
├── config.tl            # Настройки, константы
├── commands/            # Каждая команда в отдельном файле
│   ├── start.tl
│   ├── shop.tl
│   └── help.tl
├── handlers/            # Обработчики сообщений и событий
│   └── messages.tl
└── services/            # Базы данных и сервисы
    └── db.tl
```

При запуске `tele run .` или `tele dev mybot/` компилятор автоматически ищет точку входа в порядке:
1. `main.tl`
2. `bot.tl`
3. `app.tl`
4. Любой файл `.tl`, содержащий блок `bot "..."` или `userbot "..."`.

---

## 4. Декларации верхнего уровня

### `token`
Задаёт токен Telegram-бота напрямую в коде (также поддерживается чтение из `.env` или флага `--token`):
```telelang
token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
```

### `bot`
Объявляет имя и режим работы бота (polling или webhook):
```telelang
// Стандартный режим polling
bot "ShopBot"

// Режим Webhook
bot "WebhookBot" {
    mode = "webhook"
    webhook_url = "https://example.com/webhook"
    webhook_port = 8443
}
```

### `userbot`
Объявляет юзербота, работающего от имени реального аккаунта Telegram (MTProto / Telethon):
```telelang
userbot "WorkerUserbot" {
    api_id = 1234567
    api_hash = "abcdef0123456789abcdef0123456789"
    session = "sessions/user_account"
}
```

### `command`
Регистрирует команду бота с опциональной проверкой прав:
```telelang
// Обычная команда
command "/start" {
    send "Привет, {user.name}!"
}

// Доступна только админу (BOT_ADMIN_ID в .env)
command "/admin" {
    only admin
    send "Секретная панель."
}

// Доступна только роли
command "/ban" {
    only role:moderator
    send "Панель модератора."
}
```

### `on message`
Обработчик любых входящих сообщений (текст, фото и т.д.):
```telelang
on message {
    if message.text == "пинг" {
        send "понг"
    }
}
```

### `function`
Пользовательские функции (поддерживают аргументы):
```telelang
function greet_user(greeting) {
    send "{greeting}, {user.name}!"
}

function show_catalog() {
    send "Каталог товаров пуст."
}
```

### `database`
Объявляет таблицу встроенной SQLite базы данных (`database/bot.db`):
```telelang
database users {
    coins: number
    rating: number
    city: text
}
```
Поля автоматически связываются с объектом `user`:
```telelang
user.coins += 50
send "Ваш баланс: {user.coins} монет."
```

### `state`
Определяет шаг диалога в машине состояний (FSM):
```telelang
state wait_city {
    save user.city = message.text
    send "Ваш город {user.city} успешно сохранён!"
}
```

### `roles`
Объявляет роли пользователей в проекте:
```telelang
roles {
    admin: [all]
    moderator: [kick, ban, mute]
    support: [tickets]
}
```

### `api`
Объявляет клиент внешнего REST API:
```telelang
api weather {
    base_url = "https://api.weather.com/v1"
    method = "GET"
    headers = {
        "Authorization": "Bearer TOKEN"
    }
}

command "/weather" {
    let res = call api weather(city = "Moscow")
    send "Температура: {res.temp}°C"
}
```

### `ai`
Подключает модель искусственного интеллекта:
```telelang
ai openai {
    model = "gpt-4o-mini"
    key = "OPENAI_API_KEY"
}

command "/ask" {
    stream reply from ai openai "{message.text}"
}
```

### `every` (планировщик)
Запуск задач по расписанию:
```telelang
every 10 minutes {
    broadcast "📢 Не забудьте забрать ежедневную награду!"
}

every 1 hours {
    log "Проверка состояния системы..."
}
```

### `antispam`
Встроенный рейт-лимитер от спама:
```telelang
antispam {
    limit = 5
    per = 10s
    action = "warn"  // "warn" предупреждает, "ignore" молча отбрасывает
}
```

### `locales`
Встроенная мультиязычность (i18n):
```telelang
locales {
    ru {
        welcome = "Привет, {user.name}!"
        shop = "Магазин"
    }
    en {
        welcome = "Hello, {user.name}!"
        shop = "Shop"
    }
}

command "/start" {
    send t("welcome")
}
```

### `inline_query`
Обработка инлайн-запросов (когда бота вызывают через `@botname запрос`):
```telelang
inline_query {
    result "Приветствие" {
        content = "Привет от TeleLang!"
    }
    result "Справка" {
        content = "Используйте команды /start и /menu"
    }
}
```

### `import`
Импорт отдельных файлов и целых папок:
```telelang
// Импорт файла
import "services/db.tl" as db

// Импорт всех .tl файлов из директории (Auto-discovery)
import "commands/"
import "handlers/"
```

---

## 5. События и Хуки (Middlewares)

### `before_command` и `after_command`
Выполняются до и после каждой команды бота:
```telelang
before_command {
    log "Пользователь {user.id} вызвал команду: {message.text}"
}

after_command {
    log "Команда выполнена успешно."
}
```

### `on_error`
Глобальный перехватчик любых ошибок выполнения:
```telelang
on_error {
    send "Произошла непредвиденная ошибка. Мы уже разбираемся!"
    log "Ошибка в обработчике: {message.text}"
}
```

### `on_member_join` и `on_member_leave`
События входа и выхода участников из группы/канала:
```telelang
on_member_join {
    send "Добро пожаловать в группу, {user.name}!"
}

on_member_leave {
    send "Пользователь {user.name} покинул чат."
}
```

### `on_payment`
Срабатывает при успешной оплате (например, через Telegram Stars):
```telelang
on_payment {
    user.coins += 100
    send "Спасибо за покупку, {user.name}! Вам начислено 100 монет."
}
```

### `on_join_request`
Заявки на вступление в закрытый канал:
```telelang
on_join_request {
    send "Ваша заявка принята!"
}
```

### `on_poll_answer`
Ответ пользователя в опросе:
```telelang
on_poll_answer {
    log "Пользователь {user.name} ответил в опросе."
}
```

### `on_checklist_task_done`
Отметка выполнения пункта в интерактивном чек-листе:
```telelang
on_checklist_task_done {
    send "Отличная работа, пункт выполнен!"
}
```

---

## 6. Инструкции и действия (Statements)

### `send`, `send photo`, `video_note`, `document`
Отправка текста и медиа:
```telelang
send "Текстовое сообщение"
send photo "assets/logo.png" with "Подпись к фото"
send video_note "assets/circle.mp4"
send document "assets/report.pdf"
```

### `send to`
Отправка сообщения в конкретный чат по ID:
```telelang
send to 123456789 "Персональное уведомление"
```

### `broadcast`
Рассылка сообщения всем пользователям, зарегистрированным в базе данных `database`:
```telelang
broadcast "📢 Важное объявление для всех!"
```

### `buttons` (Inline кнопки и URL)
Блок кнопок под сообщением:
```telelang
buttons {
    "Купить" -> buy_item()
    "Баланс" -> check_balance()
    "Сайт" -> url("https://telegram.org")
}
```

### `ask` и `save`
Запуск FSM-диалога:
```telelang
command "/ask_name" {
    ask "Введите ваше имя:"
    state step_name
}

state step_name {
    save user.name = message.text
    send "Записал: {user.name}"
}
```

### `react` и `remove reaction`
Эмодзи-реакции на сообщения:
```telelang
react message with "👍"
remove reaction from message
```

### `send poll` и `send quiz`
Создание опросов и викторин:
```telelang
send poll "Ваш любимый язык?" {
    options = ["TeleLang", "Python", "Go"]
    is_anonymous = true
}

send quiz "Сколько бит в байте?" {
    options = ["4", "8", "16"]
    correct = 1
}
```

### `send checklist`
Интерактивный список дел с кнопками выполнения:
```telelang
send checklist "План запуска:" {
    tasks = ["Настроить бота", "Загрузить базу", "Запустить в Docker"]
}
```

### `send rich`
Форматированные информационные карточки:
```telelang
send rich {
    heading "Статистика сервера"
    paragraph "Все системы работают штатно."
    quote "Uptime: 99.9%"
    code "tele run ."
}
```

### `send_invoice`
Выставление счёта на оплату в звёздах Telegram Stars:
```telelang
send_invoice {
    title = "VIP Статус"
    description = "Доступ к премиум-функциям на 30 дней"
    price = 50 stars
}
```

### `stream reply from ai`
Потоковая генерация ответа от ИИ с эффектом печатания:
```telelang
stream reply from ai openai "Объясни квантовую физику простыми словами"
```

### `let`, `if / else`, присваивания и операции
```telelang
let x = 10
let name = "Иван"

user.coins += 15
user.coins -= 5

if user.coins >= 100 {
    send "Вы богаты!"
} else {
    if message.text contains "купить" {
        send "Недостаточно средств."
    }
}
```

### `log`
Вывод отладочной информации в консоль:
```telelang
log "Пользователь {user.name} нажал кнопку."
```

---

## 7. Контекстные переменные и операторы

| Переменная | Тип | Описание |
| :--- | :--- | :--- |
| `user.id` | `int` | Telegram ID пользователя |
| `user.name` | `string` | Полное имя пользователя |
| `user.username` | `string` | Юзернейм пользователя без `@` |
| `user.language` | `string` | Языковой код клиента (например, `ru`, `en`) |
| `user.is_premium`| `bool` | Наличие Telegram Premium |
| `user.<поле_бд>` | `number/text` | Любое поле, объявленное в таблице `database` |
| `message.text` | `string` | Текст входящего сообщения |
| `message.id` | `int` | ID сообщения в чате |
| `message.photo`| `bool` | Содержит ли сообщение фотографию |
| `chat.id` | `int` | ID чата |
| `chat.type` | `string` | Тип чата (`private`, `group`, `supergroup`, `channel`) |

Операторы условий: `==`, `!=`, `>`, `<`, `>=`, `<=`, `contains`, `not`.  
Интерполяция строк: `"Привет, {user.name}! Твой баланс: {user.coins}"`.

---

## 8. Docker & Деплой (`tele docker`)

Чтобы задеплоить проект на любой сервер или VPS, выполните:
```bash
tele docker .
```
TeleLang автоматически создаст в проекте:
1. **`Dockerfile`** — оптимизированный образ Python 3.12-slim с предустановленными зависимостями.
2. **`docker-compose.yml`** — готовый сценарий с перезапуском и сохранением базы данных `database/`.
3. **`.dockerignore`** — исключение лишних файлов.

Запуск на сервере:
```bash
docker compose up -d --build
```

---

## 9. Сборка в чистый Python (`tele build`)

Если требуется получить независимый Python-проект:
```bash
tele build mybot/
```
Создаётся зеркальная директория **`mybot_py/`**:
- `main.py` — создание `Bot`, `Dispatcher`, подключение роутеров.
- `commands/`, `handlers/`, `services/` с файлами `aiogram.Router` и `__init__.py`.
- `requirements.txt` (`aiogram>=3.0.0`, `aiosqlite`, `python-dotenv`).
- `README.md`.

Запуск без установленного TeleLang:
```bash
cd mybot_py
pip install -r requirements.txt
python main.py
```

---

## 10. Локальное тестирование без сети (`tele test`)

Интерактивный локальный симулятор диалога прямо в терминале:
```bash
tele test main.tl
```
Позволяет вводить команды, отправлять текстовые сообщения и кликать по сгенерированным инлайн-кнопкам прямо в консоли без необходимости подключать бота к Telegram.

