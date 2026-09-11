# TeleLang — Опросы, квизы, rich messages и платежи Stars (Этап 4)

token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"

bot "InteractiveShowcaseBot"

locales {
    ru {
        welcome = "Привет! Выбери интерактивную функцию:"
    }
    en {
        welcome = "Hello! Choose an interactive feature:"
    }
}

command "/poll" {
    send poll "Какой язык программирования лучше для ботов?" {
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
        paragraph "Ниже приведены ключевые показатели платформы:"
        quote "TeleLang делает создание ботов элементарным!"
    }
}

command "/donate" {
    send_invoice {
        title = "Поддержать автора"
        description = "Спасибо за звёзды Telegram!"
        price = 50 stars
    }
}

on_payment {
    send "Огромное спасибо за поддержку проекта, {user.name}! ⭐"
}

