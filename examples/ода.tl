# Пример бота с токеном прямо в коде TeleLang

token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"

bot "DirectTokenBot"

command "/start" {
    send "Привет, токен задан прямо в коде!"
}
