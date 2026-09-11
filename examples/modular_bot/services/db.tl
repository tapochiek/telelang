# Схема базы данных SQLite и методы работы с балансом

database users {
    coins: number
    name: text
}

function add_coins(amount) {
    user.coins += amount
    send "✅ Ваш баланс пополнен на {amount} монет!"
}
