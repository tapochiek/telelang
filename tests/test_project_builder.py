"""Тесты для Модульной сборки проектов и пакетной трансляции в Python (Этап 5)."""

from __future__ import annotations
import py_compile
import tempfile
import unittest
from pathlib import Path

from telelang.compiler import ProjectLoader, TeleCompiler
from telelang.codegen.project_emitter import ProjectEmitter
from telelang.cli.main import handle_build, handle_check


class TestProjectBuilder(unittest.TestCase):
    """Тестирование модульных многофайловых проектов и пакетного компилятора."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_project_loader_resolution(self):
        """Проверка автоматического обнаружения точки входа в директории."""
        project_dir = self.root / "my_shop_bot"
        project_dir.mkdir()
        main_tl = project_dir / "main.tl"
        main_tl.write_text('bot "MyShop"\ncommand "/start" { send "Привет!" }\n', encoding="utf-8")

        # 1. Разрешение по пути к директории
        entry, pdir, name = ProjectLoader.resolve_target(project_dir)
        self.assertEqual(entry, main_tl)
        self.assertEqual(pdir, project_dir)
        self.assertEqual(name, "my_shop_bot")

        # 2. Разрешение по прямому пути к файлу
        entry2, pdir2, name2 = ProjectLoader.resolve_target(main_tl)
        self.assertEqual(entry2, main_tl)
        self.assertEqual(pdir2, project_dir)

    def test_directory_import_commands(self):
        """Проверка импорта целой папки: import 'commands/'."""
        project_dir = self.root / "modular_bot"
        project_dir.mkdir()
        commands_dir = project_dir / "commands"
        commands_dir.mkdir()

        # commands/start.tl
        (commands_dir / "start.tl").write_text(
            'command "/start" { send "Старт!" }\n',
            encoding="utf-8",
        )
        # commands/help.tl
        (commands_dir / "help.tl").write_text(
            'command "/help" { send "Справка!" }\n',
            encoding="utf-8",
        )
        # main.tl
        main_tl = project_dir / "main.tl"
        main_tl.write_text(
            'bot "Modular"\nimport "commands/"\n',
            encoding="utf-8",
        )

        prog, resolver, entry, pdir, name = TeleCompiler.load_project(project_dir)
        self.assertEqual(len(resolver.resolved_files), 3)  # main.tl, help.tl, start.tl

        # Проверяем, что обе команды попали в объединённое дерево AST
        cmd_names = [d.command for d in prog.declarations if hasattr(d, "command")]
        self.assertIn("/start", cmd_names)
        self.assertIn("/help", cmd_names)

    def test_project_emitter_structure_and_py_compile(self):
        """Проверка генерации <проект>_py и синтаксической валидности всего сгенерированного Python-кода."""
        project_dir = self.root / "cool_bot"
        project_dir.mkdir()
        commands_dir = project_dir / "commands"
        commands_dir.mkdir()
        services_dir = project_dir / "services"
        services_dir.mkdir()

        (commands_dir / "start.tl").write_text(
            'command "/start" {\n'
            '    send "Привет, {user.name}!"\n'
            '    buttons {\n'
            '        "Каталог" -> show_catalog()\n'
            '    }\n'
            '}\n'
            'function show_catalog() {\n'
            '    send "Каталог пуст."\n'
            '}\n',
            encoding="utf-8",
        )

        (services_dir / "db.tl").write_text(
            'database users {\n'
            '    coins: number\n'
            '    name: text\n'
            '}\n'
            'function add_coins(amount) {\n'
            '    user.coins += amount\n'
            '}\n',
            encoding="utf-8",
        )

        main_tl = project_dir / "main.tl"
        main_tl.write_text(
            'token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"\n'
            'bot "CoolBot"\n'
            'import "services/db.tl" as db\n'
            'import "commands/"\n',
            encoding="utf-8",
        )

        # Компилируем проект в cool_bot_py
        emitter = ProjectEmitter(project_dir)
        out_dir = emitter.emit_project()

        self.assertTrue(out_dir.exists())
        self.assertEqual(out_dir.name, "cool_bot_py")

        # Проверяем наличие всех ключевых файлов
        expected_files = [
            out_dir / "main.py",
            out_dir / "core.py",
            out_dir / "requirements.txt",
            out_dir / "README.md",
            out_dir / ".env",
            out_dir / "commands" / "__init__.py",
            out_dir / "commands" / "start.py",
            out_dir / "services" / "__init__.py",
            out_dir / "services" / "db.py",
        ]

        for ef in expected_files:
            self.assertTrue(ef.exists(), f"Файл {ef} должен существовать в проекте.")

        # Проверяем синтаксическую корректность каждого .py файла через py_compile
        for py_file in out_dir.rglob("*.py"):
            try:
                py_compile.compile(str(py_file), doraise=True)
            except py_compile.PyCompileError as e:
                self.fail(f"Ошибка компиляции сгенерированного файла {py_file}:\n{e}")

        # Проверяем содержимое main.py
        main_code = (out_dir / "main.py").read_text(encoding="utf-8")
        self.assertIn("from commands import router as commands_router", main_code)
        self.assertIn("dp.include_router(commands_router)", main_code)
        self.assertIn("await init_db()", main_code)

        # Проверяем router в commands/start.py
        start_code = (out_dir / "commands" / "start.py").read_text(encoding="utf-8")
        self.assertIn("router = Router(name='start')", start_code)
        self.assertTrue("Command('start')" in start_code or 'Command("start")' in start_code)

    def test_cli_build_and_check_directory(self):
        """Проверка CLI-команд tele build <dir> и tele check <dir>."""
        project_dir = self.root / "cli_test_bot"
        project_dir.mkdir()
        (project_dir / "main.tl").write_text(
            'token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"\nbot "CliBot"\ncommand "/ping" { send "pong" }\n',
            encoding="utf-8",
        )

        # tele check <dir>
        check_code = handle_check(str(project_dir))
        self.assertEqual(check_code, 0)

        # tele build <dir>
        build_code = handle_build(str(project_dir))
        self.assertEqual(build_code, 0)

        out_dir = self.root / "cli_test_bot_py"
        self.assertTrue(out_dir.exists())
        self.assertTrue((out_dir / "main.py").exists())


if __name__ == "__main__":
    unittest.main()
