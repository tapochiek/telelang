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

## 7. Команды консоли `tele`

| Команда | Описание |
| :--- | :--- |
| `tele run bot.tl` | Прямой запуск бота или юзербота в продакшене |
| `tele dev bot.tl` | Режим разработки с мгновенным hot-reload при сохранении |
| `tele test bot.tl` | **Интерактивный локальный эмулятор (Dry-Run)** в терминале без подключения к Telegram |
| `tele stats bot.tl` | Просмотр аналитики и состояния базы данных проекта |
| `tele check bot.tl` | Проверка синтаксиса, семантики и циклических импортов |
| `tele build bot.tl` | Экспорт в чистый Python-код (`aiogram 3` / `Telethon`) |
| `tele init [name]` | Генерация готовой структуры проекта со всеми каталогами |
| `tele format bot.tl` | Автоформатирование кода `.tl` |

