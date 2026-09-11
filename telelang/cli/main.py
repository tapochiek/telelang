"""Командный интерфейс (CLI) TeleLang — утилита tele."""

from __future__ import annotations
import argparse
import sys
from pathlib import Path
from typing import Optional

# Настройка UTF-8 вывода для Windows консолей
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from telelang.compiler import TeleCompiler
from telelang.errors import TeleLangError
from telelang.runtime.runner import BotRunner

__version__ = "0.1.0-mvp"


def create_arg_parser() -> argparse.ArgumentParser:
    """Создаёт парсер аргументов командной строки."""
    parser = argparse.ArgumentParser(
        prog="tele",
        description="TeleLang — язык программирования для создания Telegram-ботов и юзерботов.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"TeleLang v{__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Команда для выполнения")

    # tele run
    run_parser = subparsers.add_parser("run", help="Запустить Telegram-бота")
    run_parser.add_argument("file", help="Путь к файлу .tl")
    run_parser.add_argument("--token", help="Токен Telegram-бота (переопределяет .env)")

    # tele dev (hot-reload)
    dev_parser = subparsers.add_parser("dev", help="Запустить бота в режиме разработки с hot-reload")
    dev_parser.add_argument("file", help="Путь к файлу .tl")
    dev_parser.add_argument("--token", help="Токен Telegram-бота (переопределяет .env)")

    # tele check
    check_parser = subparsers.add_parser("check", help="Проверить синтаксис и семантику .tl файла")
    check_parser.add_argument("file", help="Путь к файлу .tl")

    # tele build
    build_parser = subparsers.add_parser("build", help="Скомпилировать .tl файл в Python-код")
    build_parser.add_argument("file", help="Путь к файлу .tl")
    build_parser.add_argument(
        "-o", "--output",
        help="Папка или файл для сохранения сгенерированного кода (по умолчанию: generated/)",
    )

    # tele test (локальный тестовый режим dry-run)
    test_parser = subparsers.add_parser("test", help="Интерактивное локальное тестирование бота без подключения к Telegram")
    test_parser.add_argument("file", help="Путь к файлу .tl")

    # tele stats (аналитика)
    stats_parser = subparsers.add_parser("stats", help="Показать статистику и аналитику использования бота")
    stats_parser.add_argument("file", help="Путь к файлу .tl")

    # tele init / new (создание структуры проекта)
    init_parser = subparsers.add_parser("init", help="Инициализировать структуру нового TeleLang проекта")
    init_parser.add_argument("name", nargs="?", default="mybot", help="Имя проекта (папки)")

    # tele format (форматирование .tl кода)
    format_parser = subparsers.add_parser("format", help="Форматировать .tl файл")
    format_parser.add_argument("file", help="Путь к файлу .tl")

    return parser


def handle_check(target_path: str) -> int:
    """Обработка команды tele check."""
    from telelang.compiler import ProjectLoader
    try:
        entrypoint, project_dir, project_name = ProjectLoader.resolve_target(target_path)
        prog, resolver, _, _, _ = TeleCompiler.load_project(entrypoint)
        files_cnt = len(resolver.resolved_files)
        print(f"[OK] Проект '{project_name}' (точка входа: '{entrypoint.name}', файлов: {files_cnt}) успешно прошёл проверку.")
        return 0
    except TeleLangError as e:
        print(e.format_report(), file=sys.stderr)
        return 1


def handle_build(target_path: str, output_path: Optional[str] = None) -> int:
    """Обработка команды tele build."""
    from telelang.compiler import ProjectLoader
    from telelang.codegen.project_emitter import ProjectEmitter

    try:
        entrypoint, project_dir, project_name = ProjectLoader.resolve_target(target_path)

        raw_target = Path(target_path).resolve()

        # 1. Если был передан одиночный файл и указан явный output_path:
        if raw_target.is_file() and output_path:
            out = Path(output_path).resolve()
            if out.is_dir() or output_path.endswith("/") or output_path.endswith("\\") or out.suffix != ".py":
                out.mkdir(parents=True, exist_ok=True)
                target = out / f"{entrypoint.stem}.py"
            else:
                out.parent.mkdir(parents=True, exist_ok=True)
                target = out
            _, python_code = TeleCompiler.compile_file(entrypoint)
            target.write_text(python_code, encoding="utf-8")
            print(f"[OK] Успешно скомпилировано в '{target}'.")
            return 0

        # 2. По умолчанию: компиляция в автономную структуру проекта Python (<проект>_py/)
        emitter = ProjectEmitter(target_path, output_dir=output_path)
        out_dir = emitter.emit_project()
        print(f"[OK] Проект успешно скомпилирован в чистый Python: '{out_dir}'.")
        print("  Сгенерированные файлы:")
        for p in sorted(out_dir.rglob("*.py")):
            rel = p.relative_to(out_dir)
            print(f"    - {rel}")
        print("    - requirements.txt")
        print("    - README.md")
        print(f"\nДля запуска перейдите в папку и выполните:")
        print(f"  cd {out_dir.name}")
        print(f"  python main.py")
        return 0
    except TeleLangError as e:
        print(e.format_report(), file=sys.stderr)
        return 1


def handle_run(target_path: str, token: Optional[str] = None) -> int:
    """Обработка команды tele run."""
    from telelang.compiler import ProjectLoader
    try:
        entrypoint, _, _ = ProjectLoader.resolve_target(target_path)
        BotRunner.run_file(entrypoint, cli_token=token)
        return 0
    except TeleLangError as e:
        print(e.format_report(), file=sys.stderr)
        return 1


def handle_dev(target_path: str, token: Optional[str] = None) -> int:
    """Обработка команды tele dev (hot-reload)."""
    from telelang.runtime.devwatch import DevWatcher
    try:
        watcher = DevWatcher(target_path, cli_token=token)
        watcher.watch()
        return 0
    except (KeyboardInterrupt, SystemExit):
        return 0
    except TeleLangError as e:
        print(e.format_report(), file=sys.stderr)
        return 1


def main(args: Optional[list[str]] = None) -> int:
    """Точка входа CLI tele."""
    parser = create_arg_parser()
    parsed_args = parser.parse_args(args)

    if not parsed_args.command:
        parser.print_help()
        return 0

    if parsed_args.command == "run":
        return handle_run(parsed_args.file, parsed_args.token)

    if parsed_args.command == "dev":
        return handle_dev(parsed_args.file, parsed_args.token)

    if parsed_args.command == "check":
        return handle_check(parsed_args.file)

    if parsed_args.command == "build":
        return handle_build(parsed_args.file, parsed_args.output)

    if parsed_args.command == "test":
        return handle_test(parsed_args.file)

    if parsed_args.command == "stats":
        return handle_stats(parsed_args.file)

    if parsed_args.command == "init":
        return handle_init(parsed_args.name)

    if parsed_args.command == "format":
        return handle_format(parsed_args.file)

    return 0


def handle_test(target_path: str) -> int:
    """Обработка команды tele test (интерактивный локальный эмулятор)."""
    from telelang.compiler import ProjectLoader
    try:
        entrypoint, _, _ = ProjectLoader.resolve_target(target_path)
        from telelang.testing.mock_engine import MockRunner
        runner = MockRunner(entrypoint)
        runner.run_interactive()
        return 0
    except TeleLangError as e:
        print(e.format_report(), file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[Ошибка tele test]: {e}", file=sys.stderr)
        return 1


def handle_stats(target_path: str) -> int:
    """Обработка команды tele stats (аналитика использования бота)."""
    from telelang.compiler import ProjectLoader
    try:
        entrypoint, project_dir, project_name = ProjectLoader.resolve_target(target_path)
    except TeleLangError as e:
        print(e.format_report(), file=sys.stderr)
        return 1

    print("=" * 55)
    print(f"  📊 TeleLang Аналитика: {project_name} ({entrypoint.name})")
    print("=" * 55)
    db_file = project_dir / "database" / "bot.db"
    if not db_file.exists():
        print("  [Информация]: База данных бота ещё не создана (нет активности).")
        print("  Пользователей: 0")
        print("  Сообщений/команд обработано: 0")
        print("=" * 55)
        return 0

    import sqlite3
    try:
        with sqlite3.connect(db_file) as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            if cur.fetchone():
                cur.execute("SELECT COUNT(*) FROM users")
                users_cnt = cur.fetchone()[0]
            else:
                users_cnt = 0
        print(f"  Всего зарегистрированных пользователей: {users_cnt}")
        print("  Состояние базы данных: Активна (database/bot.db)")
        print("=" * 55)
        return 0
    except Exception as e:
        print(f"  Ошибка чтения аналитики: {e}")
        return 1


def handle_init(project_name: str) -> int:
    """Обработка команды tele init / tele new."""
    root = Path(project_name).resolve()
    print(f"Инициализация нового проекта TeleLang в '{root.name}'...")

    (root / "commands").mkdir(parents=True, exist_ok=True)
    (root / "database").mkdir(parents=True, exist_ok=True)
    (root / "assets").mkdir(parents=True, exist_ok=True)
    (root / "sessions").mkdir(parents=True, exist_ok=True)
    (root / "locales").mkdir(parents=True, exist_ok=True)
    (root / "generated").mkdir(parents=True, exist_ok=True)

    bot_tl = root / "bot.tl"
    if not bot_tl.exists():
        bot_tl.write_text(
            f'# TeleLang Bot Project\n\n'
            f'token = "YOUR_BOT_TOKEN_HERE"\n\n'
            f'bot "{project_name}"\n\n'
            f'command "/start" {{\n'
            f'    send "Привет, {{user.name}}! Бот успешно запущен."\n'
            f'}}\n',
            encoding="utf-8",
        )

    env_file = root / ".env"
    if not env_file.exists():
        env_file.write_text("BOT_TOKEN=\nTELEGRAM_API_ID=\nTELEGRAM_API_HASH=\nOPENAI_API_KEY=\n", encoding="utf-8")

    print(f"[OK] Проект '{root.name}' успешно создан со всей необходимой структурой!")
    print(f"  Для запуска перейдите в папку и выполните: tele dev bot.tl")
    return 0


def handle_format(file_path: str) -> int:
    """Обработка команды tele format."""
    path = Path(file_path).resolve()
    if not path.exists():
        print(f"Файл '{path}' не найден.", file=sys.stderr)
        return 1
    content = path.read_text(encoding="utf-8")
    lines = [line.rstrip() for line in content.splitlines()]
    formatted = "\n".join(lines) + "\n"
    path.write_text(formatted, encoding="utf-8")
    print(f"[OK] Файл '{path.name}' отформатирован.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
