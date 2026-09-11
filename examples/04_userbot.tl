# TeleLang — Пример Telegram-юзербота на Telethon (MTProto)
# Входные параметры подтягиваются из блока или из .env (TELEGRAM_API_ID, TELEGRAM_API_HASH)

userbot "MyUserbot" {
    api_id = 123456
    api_hash = "0123456789abcdef0123456789abcdef"
    session = "sessions/my_account"
}

on message {
    if message.text == "ping" {
        send "pong"
    } else {
        if message.text == "время" {
            send "Бот на связи!"
        }
    }
}
