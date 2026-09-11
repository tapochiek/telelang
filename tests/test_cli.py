"""Тесты командного интерфейса (CLI tele)."""

import tempfile
import unittest
from pathlib import Path
from telelang.cli.main import main


class TestCLI(unittest.TestCase):
    def test_cli_check_success(self):
        with tempfile.NamedTemporaryFile(suffix=".tl", mode="w", encoding="utf-8", delete=False) as f:
            f.write('bot "TestBot"\ncommand "/start" { send "Привет!" }\n')
            temp_path = f.name

        try:
            exit_code = main(["check", temp_path])
            self.assertEqual(exit_code, 0)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_cli_check_syntax_error(self):
        with tempfile.NamedTemporaryFile(suffix=".tl", mode="w", encoding="utf-8", delete=False) as f:
            f.write('bot "TestBot"\ncommand "/start" { send }\n')
            temp_path = f.name

        try:
            exit_code = main(["check", temp_path])
            self.assertEqual(exit_code, 1)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_cli_build(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tl_file = Path(tmpdir) / "test_bot.tl"
            tl_file.write_text('bot "TestBot"\ncommand "/start" { send "Привет!" }\n', encoding="utf-8")

            out_dir = Path(tmpdir) / "out"
            exit_code = main(["build", str(tl_file), "-o", str(out_dir)])
            self.assertEqual(exit_code, 0)

            built_py = out_dir / "test_bot.py"
            self.assertTrue(built_py.exists())
            content = built_py.read_text(encoding="utf-8")
            self.assertIn("aiogram", content)
            self.assertIn("Command('start')", content)


if __name__ == "__main__":
    unittest.main()
