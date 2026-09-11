# TeleLang — ИИ-интеграция и потоковый вывод ответа (Этап 4)

token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"

bot "AiAssistantBot"

ai openai {
    model = "gpt-4o-mini"
    key = "OPENAI_API_KEY"
}

command "/start" {
    send "Привет, {user.name}! Напиши /ask и свой вопрос, чтобы получить ответ от нейросети с живым потоковым выводом."
}

command "/ask" {
    stream reply from ai openai "{message.text}"
}
