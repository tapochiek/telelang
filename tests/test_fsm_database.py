"""Тесты для FSM состояний и базы данных SQLite."""

import ast
import unittest
from telelang.compiler import TeleCompiler


class TestFSMDatabase(unittest.TestCase):
    def test_emit_fsm_and_database(self):
        code = '''
        bot "BankBot"

        database users {
            coins: number
            name: text
        }

        command "/register" {
            ask "Как тебя зовут?"
            state register_name
        }

        state register_name {
            save user.name = message.text
            user.coins += 100
            send "Готово! Тебе начислено 100 монет."
        }
        '''
        _, py_code = TeleCompiler.compile_source(code)

        # Проверяем синтаксическую корректность Python
        parsed = ast.parse(py_code)
        self.assertIsNotNone(parsed)

        # Проверяем FSM
        self.assertIn("class _TeleStates(StatesGroup):", py_code)
        self.assertIn("register_name = State()", py_code)
        self.assertIn("@router.message(_TeleStates.register_name)", py_code)
        self.assertIn("await state.set_state(_TeleStates.register_name)", py_code)
        self.assertIn("await state.clear()", py_code)

        # Проверяем SQLite
        self.assertIn("CREATE TABLE IF NOT EXISTS users", py_code)
        self.assertIn("coins REAL DEFAULT 0", py_code)
        self.assertIn("name TEXT DEFAULT ''", py_code)
        self.assertIn("await _set_user_db(user.id, 'name', message.text)", py_code)
        self.assertIn("await _update_user_db(user.id, 'coins', 100)", py_code)


if __name__ == "__main__":
    unittest.main()
