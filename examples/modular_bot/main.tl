# Точка входа модульного проекта Telegram-бота
token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"

bot "ModularShopBot"

# Подключение модулей базы данных, команд и обработчиков
import "services/db.tl" as db
import "commands/"
import "handlers/"
