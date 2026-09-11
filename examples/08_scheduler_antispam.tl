# TeleLang — Планировщик задач, рассылки и антиспам (Этап 4)

token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"

bot "SchedulerBot"

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
    broadcast "📢 Плановое уведомление: бот работает в штатном режиме!"
}

command "/start" {
    send "Добро пожаловать, {user.name}! Ты добавлен в список рассылки."
}

