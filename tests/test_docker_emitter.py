"""Тесты для команды tele docker и модуля DockerEmitter."""

from __future__ import annotations
import tempfile
import unittest
from pathlib import Path

from telelang.codegen.docker_emitter import DockerEmitter
from telelang.cli.main import handle_docker


class TestDockerEmitter(unittest.TestCase):
    """Тестирование генерации Dockerfile, docker-compose.yml и .dockerignore."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_docker_emitter_files(self):
        """Проверка содержимого сгенерированных файлов Docker."""
        project_dir = self.root / "my_bot"
        project_dir.mkdir()

        df, dc, di = DockerEmitter.emit(project_dir, "My_Bot", is_userbot=False)

        self.assertTrue(df.exists())
        self.assertTrue(dc.exists())
        self.assertTrue(di.exists())

        # Проверка Dockerfile
        df_content = df.read_text(encoding="utf-8")
        self.assertIn("FROM python:3.12-slim", df_content)
        self.assertIn("WORKDIR /app", df_content)
        self.assertIn("pip install", df_content)
        self.assertIn("telelang.cli.main", df_content)

        # Проверка docker-compose.yml
        dc_content = dc.read_text(encoding="utf-8")
        self.assertIn("version:", dc_content)
        self.assertIn("my_bot_bot:", dc_content)
        self.assertIn("restart: unless-stopped", dc_content)
        self.assertIn("./database:/app/database", dc_content)
        self.assertIn("env_file:", dc_content)

        # Проверка .dockerignore
        di_content = di.read_text(encoding="utf-8")
        self.assertIn("__pycache__/", di_content)
        self.assertIn(".git/", di_content)

    def test_cli_docker_command(self):
        """Проверка CLI команды tele docker <path>."""
        project_dir = self.root / "cli_bot"
        project_dir.mkdir()
        (project_dir / "main.tl").write_text(
            'token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"\nbot "CliBot"\ncommand "/start" { send "hi" }\n',
            encoding="utf-8",
        )

        exit_code = handle_docker(str(project_dir))
        self.assertEqual(exit_code, 0)

        self.assertTrue((project_dir / "Dockerfile").exists())
        self.assertTrue((project_dir / "docker-compose.yml").exists())
        self.assertTrue((project_dir / ".dockerignore").exists())


if __name__ == "__main__":
    unittest.main()
