# TeleLang — Бот с базой данных SQLite и машиной состояний (FSM)

token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"

bot "BankBot"

database users {
    coins: number
    name: text
}

command "/start" {
    send "Привет, {user.name}! Твой баланс: {user.coins} монет.\nДля регистрации напиши /register, для бонуса — /daily"
}

command "/daily" {
    user.coins += 50
    send "🎁 Ты получил 50 бонусных монет! Текущий баланс: {user.coins}"
}

command "/register" {
    ask "Как тебя зовут?"
    state register_name
}

state register_name {
    save user.name = message.text
    user.coins += 100
    send "Отлично, {user.name}! Ты успешно зарегистрирован и получил приветственные 100 монет."
}
