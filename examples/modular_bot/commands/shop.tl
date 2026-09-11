# Каталог товаров и проверка баланса

function show_catalog() {
    send "📦 Доступные товары:\n1. 🌟 Премиум доступ — 100 монет\n2. 💎 VIP статус — 500 монет\n\nИспользуйте команду /buy для оформления."
}

function show_balance() {
    send "💰 Ваш текущий баланс: {user.coins} монет"
}

command "/shop" {
    show_catalog()
}

command "/balance" {
    show_balance()
}
