"""Тесты для режима юзербота (Telethon / MTProto)."""

import ast
import unittest
from telelang.compiler import TeleCompiler


class TestUserbot(unittest.TestCase):
    def test_emit_valid_userbot(self):
        code = '''
        userbot "MyUserbot" {
            api_id = 123456
            api_hash = "abcdef1234567890"
            session = "sessions/test_session"
        }

        command "/ping" {
            send "pong"
        }

        on message {
            if message.text == "привет" {
                send "Привет от юзербота!"
            }
        }
        '''
        _, py_code = TeleCompiler.compile_source(code)

        # Проверяем синтаксическую валидность Python-кода
        parsed = ast.parse(py_code)
        self.assertIsNotNone(parsed)

        # Проверяем наличие ключевых компонентов Telethon
        self.assertIn("from telethon import TelegramClient, events", py_code)
        self.assertIn("client = TelegramClient(session_path, api_id, api_hash)", py_code)
        self.assertIn("api_id = 123456", py_code)
        self.assertIn("api_hash = 'abcdef1234567890'", py_code)
        self.assertIn("@client.on(events.NewMessage", py_code)
        self.assertIn("await _event.respond('pong')", py_code)
        self.assertIn("async def run_userbot()", py_code)
        self.assertIn("await client.start()", py_code)


if __name__ == "__main__":
    unittest.main()
