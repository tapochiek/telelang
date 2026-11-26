# Обработчик стартовой команды с кнопками

command "/start" {
    send "👋 Привет, {user.name}!\nДобро пожаловать в модульный магазин на TeleLang."

    buttons {
        "🛒 Каталог товаров" -> show_catalog()
        "💰 Мой баланс" -> show_balance()
        "🌐 Telegram" -> url("https://telegram.org")
    }
}
