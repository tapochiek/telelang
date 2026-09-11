"""Тесты для модулей, импортов и обнаружения циклических зависимостей."""

import tempfile
import unittest
from pathlib import Path
from telelang.compiler import TeleCompiler
from telelang.errors import TeleLangSemanticError


class TestModules(unittest.TestCase):
    def test_basic_import(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            utils_file = tmp / "utils.tl"
            utils_file.write_text('function greet(name) { send "Привет, {name}!" }\n', encoding="utf-8")

            main_file = tmp / "main.tl"
            main_file.write_text('import "utils.tl"\nbot "MyBot"\ncommand "/start" { greet(user.name) }\n', encoding="utf-8")

            prog, py_code = TeleCompiler.compile_file(main_file)
            self.assertIn("async def greet", py_code)
            self.assertIn("Command('start')", py_code)

    def test_aliased_import(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            shop_file = tmp / "shop.tl"
            shop_file.write_text('function open() { send "Магазин открыт!" }\n', encoding="utf-8")

            main_file = tmp / "main.tl"
            main_file.write_text('import "shop.tl" as shop\nbot "MyBot"\ncommand "/shop" { send "Заходи" }\n', encoding="utf-8")

            prog, py_code = TeleCompiler.compile_file(main_file)
            self.assertIn("async def shop_open", py_code)

    def test_circular_import_detection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            a_file = tmp / "a.tl"
            b_file = tmp / "b.tl"

            a_file.write_text('import "b.tl"\nbot "MyBot"\n', encoding="utf-8")
            b_file.write_text('import "a.tl"\nfunction test() {}\n', encoding="utf-8")

            with self.assertRaises(TeleLangSemanticError) as ctx:
                TeleCompiler.compile_file(a_file)

            error_msg = str(ctx.exception)
            self.assertIn("Обнаружен циклический импорт", error_msg)
            self.assertIn("a.tl -> b.tl -> a.tl", error_msg)


if __name__ == "__main__":
    unittest.main()
