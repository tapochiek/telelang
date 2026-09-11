# TeleLang — Интерактивный бот с кнопками, функциями и условиями (Этап 2)

token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"

bot "InteractiveBot"

function show_profile() {
    send "👤 Твой профиль:\nИмя: {user.name}\nID: {user.id}\nUsername: @{user.username}"
}

function show_shop() {
    send "🛒 Каталог товаров пока наполняется. Загляни позже!"
}

command "/start" {
    send "Привет, {user.name}! Выбери действие ниже:"

    buttons {
        "👤 Мой профиль" -> show_profile()
        "🛒 Магазин" -> show_shop()
        "🌐 Официальный сайт" -> url("https://telegram.org")
    }
}

on message {
    if message.text == "ping" {
        send "pong"
    } else {
        if message.text contains "привет" {
            send "И тебе привет, {user.name}!"
        } else {
            send "Ты написал: {message.text}"
        }
    }
}
