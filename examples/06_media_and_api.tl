# TeleLang — Бот с медиафайлами, хуками и внешним HTTP API

token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"

bot "MediaAndApiBot"

api weather {
    url = "https://api.open-meteo.com/v1/forecast"
}

before_command {
    log "Новый запрос от пользователя {user.id}"
}

after_command {
    log "Запрос пользователя {user.id} обработан за {elapsed_ms}ms"
}

on_error {
    log_error error
    send "Произошла ошибка, попробуйте позже."
}

command "/start" {
    send "Привет! Доступные команды:\n/photo — отправить фото\n/circle — отправить видео-кружок\n/doc — отправить документ\n/weather — прогноз погоды"
}

command "/photo" {
    send photo "assets/example.jpg" {
        caption = "Демо-изображение из TeleLang"
    }
}

command "/circle" {
    send video_note "assets/circle.mp4"
}

command "/doc" {
    send document "assets/document.pdf" {
        caption = "Ваш отчёт"
    }
}

command "/weather" {
    result = call weather with { latitude: "55.75", longitude: "37.62", current_weather: "true" }
    send "Погода в Москве получена через API!"
}
