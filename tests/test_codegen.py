"""Тесты генератора кода (PythonEmitter)."""

import ast
import unittest
from telelang.compiler import TeleCompiler


class TestCodegen(unittest.TestCase):
    def test_emit_valid_python(self):
        code = '''
        bot "TestBot"

        command "/start" {
            send "Привет, мир!"
        }

        command "/help" {
            send "Справка по боту"
        }
        '''
        _, python_code = TeleCompiler.compile_source(code)

        # Проверяем, что сгенерированный код является синтаксически корректным Python-кодом
        parsed_ast = ast.parse(python_code)
        self.assertIsNotNone(parsed_ast)

        # Проверяем наличие ключевых конструкций aiogram
        self.assertIn("from aiogram import Bot, Dispatcher, Router, types", python_code)
        self.assertIn("from aiogram.filters import Command", python_code)
        self.assertIn("@router.message(Command('start'))", python_code)
        self.assertIn("@router.message(Command('help'))", python_code)
        self.assertIn("await _msg_target.answer('Привет, мир!')", python_code)
        self.assertIn("await _msg_target.answer('Справка по боту')", python_code)
        self.assertIn("def create_bot(token: str)", python_code)
        self.assertIn("async def run_bot(token: str)", python_code)


if __name__ == "__main__":
    unittest.main()
