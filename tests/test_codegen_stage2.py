"""Тесты кодогенератора для Этапа 2."""

import ast
import unittest
from telelang.compiler import TeleCompiler


class TestCodegenStage2(unittest.TestCase):
    def test_emit_buttons_and_callbacks(self):
        code = '''
        token = "123456:ABCdefGHIjklMNOpqrsTUVwxyz"

        bot "Stage2Bot"

        function show_profile() {
            send "Твой профиль: {user.name}"
        }

        command "/menu" {
            send "Главное меню:"
            buttons {
                "Профиль" -> show_profile()
                "Сайт" -> url("https://google.com")
            }
        }

        on message {
            if message.text contains "ping" {
                send "pong"
            } else {
                send "Ты написал: {message.text}"
            }
        }
        '''
        _, py_code = TeleCompiler.compile_source(code)

        # Проверяем синтаксическую валидность Python-кода
        parsed = ast.parse(py_code)
        self.assertIsNotNone(parsed)

        # Проверяем ключевые конструкции aiogram
        self.assertIn("InlineKeyboardMarkup", py_code)
        self.assertIn("InlineKeyboardButton", py_code)
        self.assertIn("router.callback_query", py_code)
        self.assertIn("router.message()", py_code)
        self.assertIn("url='https://google.com'", py_code)
        self.assertIn("async def show_profile", py_code)
        self.assertIn("_CtxUser", py_code)
        self.assertIn("_CtxMsg", py_code)


if __name__ == "__main__":
    unittest.main()
