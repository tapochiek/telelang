"""Тесты для модуля DevWatcher (tele dev)."""

import tempfile
import time
import unittest
from pathlib import Path
from telelang.runtime.devwatch import DevWatcher


class TestDevWatcher(unittest.TestCase):
    def test_file_modification_detection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bot_file = Path(tmpdir) / "test_bot.tl"
            bot_file.write_text('bot "TestBot"\ncommand "/start" { send "Привет!" }\n', encoding="utf-8")

            watcher = DevWatcher(bot_file)

            # Первый опрос — инициализация mtime
            changed = watcher.check_for_changes()
            self.assertFalse(changed)

            # Изменяем файл
            time.sleep(0.05)
            bot_file.write_text('bot "TestBot"\ncommand "/start" { send "Обновлено!" }\n', encoding="utf-8")

            # Второй опрос — изменение должно быть зафиксировано
            changed = watcher.check_for_changes()
            self.assertTrue(changed)


if __name__ == "__main__":
    unittest.main()
