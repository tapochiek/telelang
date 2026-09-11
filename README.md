# TeleLang (Этап 4 — Финальный релиз)

**TeleLang** — предметно-ориентированный язык программирования (DSL), созданный для предельно простой разработки полнофункциональных Telegram-ботов (на `aiogram 3`) и юзерботов (на `Telethon` MTProto).

---

## 1. Режимы работы: Bot и Userbot

### Режим Bot (Telegram Bot API / aiogram 3)
```telelang
token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"

bot "MyBot"

command "/start" {
    send "Привет, {user.name}!"
}
```

### Режим Userbot (MTProto / Telethon)
Работает от имени реального Telegram-аккаунта (сессии сохраняются в папку `sessions/`):
```telelang
userbot "MyUserbot" {
    api_id = 123456
    api_hash = "abcdef0123456789"
    session = "sessions/my_session"
}

on message {
    if message.text == "ping" {
        send "pong"
    }
}
```

---

## 2. ИИ-интеграции и потоковый вывод (`ai {}`, `stream`)

```telelang
bot "AiBot"

ai openai {
    model = "gpt-4o-mini"
    key = "OPENAI_API_KEY"
}

command "/ask" {
    stream reply from ai openai "{message.text}"
}
```

---

## 3. Планировщик задач, Рассылка и Антиспам

```telelang
bot "CronBot"

database users {
    coins: number
    name: text
}

antispam {
    limit = 5
    per = 10s
    action = "warn"
}

every 10 minutes {
    broadcast "📢 Плановое уведомление всем пользователям!"
}
```

---

## 4. Опросы, Квизы, Rich Messages и Платежи Stars

```telelang
command "/poll" {
    send poll "Какой язык лучше?" {
        options = ["Python", "TeleLang", "Go"]
    }
}

command "/quiz" {
    send quiz "В каком году появился Telegram?" {
        options = ["2011", "2013", "2015"]
        correct = 1
    }
}

command "/rich" {
    send rich {
        heading "Статистика проекта"
        paragraph "Платформа работает стабильно."
        quote "TeleLang делает создание ботов элементарным!"
    }
}

command "/donate" {
    send_invoice {
        title = "Поддержать проект"
        description = "Спасибо за звёзды!"
        price = 50 stars
    }
}

on_payment {
    send "Спасибо за покупку, {user.name}! ⭐"
}
```

---

## 5. Мультиязычность (i18n)

```telelang
locales {
    ru {
        welcome = "Привет, {user.name}!"
    }
    en {
        welcome = "Hello, {user.name}!"
    }
}

command "/start" {
    send t("welcome")
}
```

---

## 6. База данных SQLite и FSM

```telelang
database users {
    coins: number
    name: text
}

command "/daily" {
    user.coins += 50
    send "Баланс: {user.coins}"
}

command "/register" {
    ask "Как тебя зовут?"
    state register_name
}

state register_name {
    save user.name = message.text
    user.coins += 100
    send "Добро пожаловать, {user.name}!"
}
```

---

## 7. Модульная архитектура проектов и компиляция в Python (`<проект>_py`)

TeleLang позволяет организовывать большие проекты с привычной структурой каталогов (как в Python, Go или NodeJS):
```
mybot/
├── main.tl              # Главный файл: токен, имя бота, импорты
├── commands/            # Папка команд (каждая в своем файле)
│   ├── start.tl
│   └── shop.tl
├── handlers/            # Папка хэндлеров
│   └── messages.tl
└── services/            # Базы данных и бизнес-логика
    └── db.tl
```

### Точка входа `main.tl`:
```telelang
token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
bot "ModularBot"

// Подключение целых папок одной строкой
import "services/db.tl" as db
import "commands/"
import "handlers/"
```

### Сборка в чистый автономный Python-проект:
```bash
tele build mybot/
# или
tele build main.tl
```
TeleLang автоматически генерирует полностью готовую автономную директорию **`mybot_py/`**:
- `main.py` — создание `Bot`, `Dispatcher`, подключение роутеров.
- `commands/`, `handlers/`, `services/` с `__init__.py` и `aiogram.Router`.
- `requirements.txt` (`aiogram>=3.0.0`, `aiosqlite>=0.19.0`, `python-dotenv>=1.0.0`).
- `README.md` с инструкцией запуска через `python main.py`.

---

## 8. Команды консоли `tele`

| Команда | Описание |
| :--- | :--- |
| `tele run main.tl` или `tele run .` | Запуск бота/юзербота (принимает файл или директорию) |
| `tele dev main.tl` или `tele dev .` | Режим разработки с рекурсивным hot-reload всех файлов и подпапок |
| `tele build mybot/` или `tele build main.tl` | Компиляция в автономную структуру **`mybot_py/`** на чистом Python |
| `tele test main.tl` или `tele test .` | **Интерактивный локальный эмулятор** без подключения к Telegram |
| `tele stats main.tl` или `tele stats .` | Просмотр аналитики и состояния базы данных проекта |
| `tele check main.tl` или `tele check .` | Проверка синтаксиса, семантики и циклических импортов всего проекта |
| `tele init [name]` | Генерация структуры нового проекта со всеми каталогами |
| `tele format file.tl` | Автоформатирование исходного кода `.tl` |

