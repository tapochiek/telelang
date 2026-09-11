"""Модульный транслятор проектов TeleLang в чистый Python (aiogram 3.x).

Генерирует автономную структуру проекта в директории `<имя_проекта>_py/` с сохранением
архитектуры папок (commands/, handlers/, services/), роутеров aiogram.Router,
requirements.txt, main.py и README.md.
"""

from __future__ import annotations
import os
import shutil
from pathlib import Path
from typing import Optional

from telelang.codegen.python_emitter import PythonEmitter
from telelang.compiler import TeleCompiler
from telelang.errors import SourceSpan
from telelang.parser.ast_nodes import (
    BotDecl,
    CommandDecl,
    DatabaseDecl,
    FunctionDecl,
    OnMessageDecl,
    Program,
    StateDecl,
    UserbotDecl,
    VariableAssignStmt,
)


class ProjectEmitter:
    """Генератор автономного Python-проекта из проекта TeleLang."""

    def __init__(
        self,
        target_path: str | Path,
        output_dir: Optional[str | Path] = None,
    ):
        self.target_path = Path(target_path).resolve()
        (
            self.merged_prog,
            self.resolver,
            self.entrypoint,
            self.project_dir,
            self.project_name,
        ) = TeleCompiler.load_project(self.target_path)

        if output_dir:
            self.output_dir = Path(output_dir).resolve()
        else:
            self.output_dir = self.project_dir.parent / f"{self.project_name}_py"

    def emit_project(self) -> Path:
        """Выполняет полную компиляцию проекта в структуру каталогов Python."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        is_userbot = any(isinstance(d, UserbotDecl) for d in self.merged_prog.declarations)
        bot_decl = next((d for d in self.merged_prog.declarations if isinstance(d, BotDecl)), None)
        bot_name = bot_decl.name if bot_decl else self.project_name

        # Токен бота
        token_val = self._extract_token()

        # 1. Генерация core.py (общий контекст, FSM состояния, слой базы данных)
        self._emit_core_module()

        # 2. Компиляция каждого отдельного файла проекта в соответствующий .py файл
        package_routers: dict[str, list[str]] = {}  # folder_name -> [module_name, ...]
        toplevel_routers: list[str] = []

        for file_path in self.resolver.resolved_files:
            if file_path == self.entrypoint:
                continue

            rel_path = file_path.relative_to(self.project_dir)
            target_py = self.output_dir / rel_path.with_suffix(".py")
            target_py.parent.mkdir(parents=True, exist_ok=True)

            file_prog = self.resolver.file_programs.get(file_path, Program(declarations=[], span=SourceSpan(1, 1)))
            has_router = self._emit_child_module(file_prog, target_py, rel_path.stem)

            # Регистрация роутера
            if has_router:
                if len(rel_path.parts) > 1:
                    folder_name = rel_path.parts[0]
                    package_routers.setdefault(folder_name, []).append(rel_path.stem)
                else:
                    toplevel_routers.append(rel_path.stem)

        # 3. Создание __init__.py в поддиректориях для объединения роутеров
        self._emit_package_inits(package_routers)

        # 4. Генерация main.py
        self._emit_main_module(bot_name, token_val, package_routers, toplevel_routers, is_userbot)

        # 5. Генерация requirements.txt
        self._emit_requirements(is_userbot)

        # 6. Генерация .env
        self._emit_dotenv(token_val)

        # 7. Генерация README.md
        self._emit_readme(bot_name)

        return self.output_dir

    def _extract_token(self) -> str:
        """Извлекает токен бота из AST или .env."""
        # 1. Проверка явного присваивания token = "..." в коде
        for decl in self.merged_prog.declarations:
            if isinstance(decl, VariableAssignStmt) and decl.var_name == "token":
                from telelang.parser.ast_nodes import StringLiteral
                if isinstance(decl.value, StringLiteral):
                    return decl.value.value

        # 2. Проверка .env файла в исходном проекте
        env_file = self.project_dir / ".env"
        if env_file.exists():
            try:
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    if line.startswith("BOT_TOKEN=") and len(line) > 10:
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
            except Exception:
                pass

        return "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"

    def _emit_core_module(self) -> None:
        """Генерирует core.py со служебными классами контекста, FSM и SQLite."""
        core_file = self.output_dir / "core.py"
        emitter = PythonEmitter(self.merged_prog)
        emitter.emit()  # Парсит декларации программы в свойства emitter

        lines = [
            "# -*- coding: utf-8 -*-",
            "# Сгенерировано компилятором TeleLang (Ядро проекта)",
            "import os",
            "import sys",
            "from pathlib import Path",
            "import aiosqlite",
            "from aiogram.fsm.state import State, StatesGroup",
            "",
            "# Определение путей базы данных",
            "BASE_DIR = Path(__file__).resolve().parent",
            "DB_PATH = BASE_DIR / 'database' / 'bot.db'",
            "",
            "class _DotDict(dict):",
            "    def __getattr__(self, name):",
            "        val = self.get(name)",
            "        if isinstance(val, dict):",
            "            return _DotDict(val)",
            "        return val",
            "    def __setattr__(self, name, value):",
            "        self[name] = value",
            "",
            "class _CtxUser:",
            "    def __init__(self, u):",
            "        self.id = u.id if u else 0",
            "        self.name = (u.full_name or '') if u else ''",
            "        self.username = (u.username or '') if u else ''",
            "        self.language = (u.language_code or '') if u else ''",
            "        self.is_premium = bool(u.is_premium) if u else False",
            "        self.coins = 0",
            "    def __str__(self):",
            "        return self.name",
            "",
            "class _CtxMsg:",
            "    def __init__(self, m):",
            "        self.id = m.message_id if m else 0",
            "        self.text = (m.text or '') if m else ''",
            "        self.photo = bool(m.photo) if m else False",
            "    def __str__(self):",
            "        return self.text",
            "",
            "class _CtxChat:",
            "    def __init__(self, c):",
            "        self.id = c.id if c else 0",
            "        self.type = c.type if c else 'private'",
            "    def __str__(self):",
            "        return str(self.id)",
            "",
        ]

        # FSM Состояния
        if emitter.states:
            lines.append("class _TeleStates(StatesGroup):")
            for st in emitter.states:
                lines.append(f"    {st.name} = State()")
            lines.append("")
        else:
            lines.append("class _TeleStates(StatesGroup):")
            lines.append("    pass\n")

        # База данных SQLite
        lines.append("async def init_db():")
        lines.append("    DB_PATH.parent.mkdir(parents=True, exist_ok=True)")
        lines.append("    async with aiosqlite.connect(DB_PATH) as db:")
        if emitter.databases:
            for db_decl in emitter.databases:
                col_defs = ["user_id INTEGER PRIMARY KEY"]
                for f_name, f_type in db_decl.fields.items():
                    sql_type = "REAL DEFAULT 0" if f_type == "number" else "TEXT DEFAULT ''"
                    col_defs.append(f"{f_name} {sql_type}")
                cols_str = ", ".join(col_defs)
                lines.append(f"        await db.execute('CREATE TABLE IF NOT EXISTS {db_decl.table_name} ({cols_str})')")
        else:
            lines.append("        await db.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, coins REAL DEFAULT 0, name TEXT DEFAULT \\'\\')')")
        lines.extend([
            "        await db.execute('CREATE TABLE IF NOT EXISTS user_roles (user_id INTEGER, role TEXT, PRIMARY KEY(user_id, role))')",
            "        await db.commit()",
            "",
            "async def _get_user_db(user_id: int, field: str, default=0):",
            "    async with aiosqlite.connect(DB_PATH) as db:",
            "        db.row_factory = aiosqlite.Row",
            "        async with db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)) as cur:",
            "            row = await cur.fetchone()",
            "            if row and field in row.keys():",
            "                return row[field]",
            "    return default",
            "",
            "async def _set_user_db(user_id: int, field: str, value):",
            "    async with aiosqlite.connect(DB_PATH) as db:",
            "        await db.execute('INSERT INTO users (user_id, ' + field + ') VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET ' + field + ' = excluded.' + field, (user_id, value))",
            "        await db.commit()",
            "",
            "async def _update_user_db(user_id: int, field: str, delta):",
            "    curr = await _get_user_db(user_id, field, 0)",
            "    await _set_user_db(user_id, field, curr + delta)",
            "",
        ])

        # Внешние API функции
        for api in emitter.apis:
            lines.extend(emitter._emit_api_client(api))
            lines.append("")

        # Локализация
        if emitter.locales:
            lines.extend(emitter._emit_locales_layer(emitter.locales))
            lines.append("")

        core_file.write_text("\n".join(lines), encoding="utf-8")

    def _emit_child_module(self, prog: Program, target_py: Path, module_name: str) -> bool:
        """Компилирует один модуль проекта в файл .py с Router'ом или сервисными функциями."""
        emitter = PythonEmitter(prog)
        emitter.emit()

        has_router = bool(emitter.commands or emitter.on_messages or emitter.callbacks or emitter.states)

        lines = [
            "# -*- coding: utf-8 -*-",
            f"# Сгенерировано компилятором TeleLang: модуль '{module_name}'",
            "import os",
            "import sys",
            "from pathlib import Path",
            "import aiosqlite",
            "from aiogram import Router, types, F",
            "from aiogram.filters import Command",
            "from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile",
            "from aiogram.fsm.context import FSMContext",
            "",
            "from core import _CtxUser, _CtxMsg, _CtxChat, _DotDict, _TeleStates, DB_PATH, _get_user_db, _set_user_db, _update_user_db",
            "",
        ]

        if has_router:
            clean_tag = module_name.replace("-", "_").replace(".", "_")
            lines.append(f"router = Router(name={clean_tag!r})\n")

        # Функции
        for fn in emitter.functions:
            lines.extend(emitter._emit_user_function(fn))
            lines.append("")

        # Команды
        for idx, cmd in enumerate(emitter.commands):
            lines.extend(emitter._emit_command(cmd, idx))
            lines.append("")

        # Обработчики FSM состояний
        for st in emitter.states:
            lines.extend(emitter._emit_state_handler(st))
            lines.append("")

        # On message
        for idx, on_msg in enumerate(emitter.on_messages):
            lines.extend(emitter._emit_on_message(on_msg, idx))
            lines.append("")

        # Callbacks
        for cb_id, _, call_expr in emitter.callbacks:
            lines.extend(emitter._emit_callback_handler(cb_id, call_expr))
            lines.append("")

        target_py.write_text("\n".join(lines), encoding="utf-8")
        return has_router

    def _emit_package_inits(self, package_routers: dict[str, list[str]]) -> None:
        """Создаёт __init__.py для пакетов проекта."""
        # Обработка директорий с роутерами
        for folder, mod_names in package_routers.items():
            init_file = self.output_dir / folder / "__init__.py"
            lines = [
                "# -*- coding: utf-8 -*-",
                f"# Агрегатор роутеров для пакета '{folder}'",
                "from aiogram import Router",
            ]
            for m in mod_names:
                lines.append(f"from .{m} import router as {m}_router")

            lines.append(f"\nrouter = Router(name={folder!r})")
            for m in mod_names:
                lines.append(f"router.include_router({m}_router)")

            lines.append("\n__all__ = ['router']")
            init_file.write_text("\n".join(lines), encoding="utf-8")

        # Обработка директорий без роутеров (например, services/)
        for child_dir in self.output_dir.iterdir():
            if child_dir.is_dir() and child_dir.name not in package_routers and child_dir.name != "__pycache__":
                init_file = child_dir / "__init__.py"
                if not init_file.exists():
                    py_files = [p.stem for p in child_dir.glob("*.py") if p.name != "__init__.py"]
                    lines = ["# -*- coding: utf-8 -*-"]
                    for p in py_files:
                        lines.append(f"from .{p} import *")
                    init_file.write_text("\n".join(lines), encoding="utf-8")

    def _emit_main_module(
        self,
        bot_name: str,
        token_val: str,
        package_routers: dict[str, list[str]],
        toplevel_routers: list[str],
        is_userbot: bool,
    ) -> None:
        """Генерирует главный исполняемый файл main.py."""
        main_file = self.output_dir / "main.py"
        entry_prog = self.resolver.file_programs.get(self.entrypoint, Program(declarations=[], span=SourceSpan(1, 1)))
        entry_emitter = PythonEmitter(entry_prog)
        entry_emitter.emit()

        has_entry_router = bool(entry_emitter.commands or entry_emitter.on_messages or entry_emitter.callbacks)

        lines = [
            "# -*- coding: utf-8 -*-",
            f"# Главная точка входа бота '{bot_name}'",
            "# Сгенерировано компилятором TeleLang",
            "import asyncio",
            "import logging",
            "import os",
            "import sys",
            "from pathlib import Path",
            "from dotenv import load_dotenv",
            "",
            "from aiogram import Bot, Dispatcher, Router",
            "from aiogram.fsm.storage.memory import MemoryStorage",
            "from core import init_db",
            "",
        ]

        # Импорт роутеров из пакетов
        for pkg in package_routers.keys():
            lines.append(f"from {pkg} import router as {pkg}_router")

        # Импорт роутеров верхнего уровня
        for top_mod in toplevel_routers:
            lines.append(f"from {top_mod} import router as {top_mod}_router")

        lines.extend([
            "",
            "# Загрузка переменных окружения из .env",
            "load_dotenv()",
            "",
            f"TOKEN = os.environ.get('BOT_TOKEN', {token_val!r})",
            "",
            "logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s')",
            f"logger = logging.getLogger({bot_name!r})",
            "",
            "bot = Bot(token=TOKEN)",
            "dp = Dispatcher(storage=MemoryStorage())",
            "",
        ])

        # Подключение роутеров к диспетчеру
        for pkg in package_routers.keys():
            lines.append(f"dp.include_router({pkg}_router)")

        for top_mod in toplevel_routers:
            lines.append(f"dp.include_router({top_mod}_router)")

        # Если в самом главном файле были объявлены команды
        if has_entry_router:
            lines.append("\n# Хэндлеры, объявленные непосредственно в главном файле")
            lines.append("main_router = Router(name='main')")
            for idx, cmd in enumerate(entry_emitter.commands):
                lines.extend(entry_emitter._emit_command(cmd, idx))
                lines.append("")
            for idx, on_msg in enumerate(entry_emitter.on_messages):
                lines.extend(entry_emitter._emit_on_message(on_msg, idx))
                lines.append("")
            lines.append("dp.include_router(main_router)")

        lines.extend([
            "",
            "async def on_startup():",
            "    await init_db()",
            f"    logger.info('Бот {bot_name} успешно инициализирован и готов к работе!')",
            "",
            "async def main():",
            "    await on_startup()",
            "    await dp.start_polling(bot)",
            "",
            "if __name__ == '__main__':",
            "    try:",
            "        asyncio.run(main())",
            "    except (KeyboardInterrupt, SystemExit):",
            "        logger.info('Бот остановлен.')",
            "",
        ])

        main_file.write_text("\n".join(lines), encoding="utf-8")

    def _emit_requirements(self, is_userbot: bool) -> None:
        """Генерирует requirements.txt."""
        req_file = self.output_dir / "requirements.txt"
        pkgs = [
            "aiogram>=3.0.0",
            "aiosqlite>=0.19.0",
            "python-dotenv>=1.0.0",
            "aiohttp>=3.8.0",
        ]
        if is_userbot:
            pkgs.append("telethon>=1.30.0")
        req_file.write_text("\n".join(pkgs) + "\n", encoding="utf-8")

    def _emit_dotenv(self, token_val: str) -> None:
        """Генерирует файл .env."""
        env_file = self.output_dir / ".env"
        if not env_file.exists():
            content = f"BOT_TOKEN={token_val}\nBOT_ADMIN_ID=0\n"
            env_file.write_text(content, encoding="utf-8")

    def _emit_readme(self, bot_name: str) -> None:
        """Генерирует документацию README.md для автономного проекта."""
        readme_file = self.output_dir / "README.md"
        content = f"""# {bot_name}

Этот проект Telegram-бота был скомпилирован из языка **TeleLang** в чистый, автономный **Python (aiogram 3.x)**.

## 🚀 Установка и запуск:

### 1. Установите зависимости:
```bash
pip install -r requirements.txt
```

### 2. Настройте токен бота:
Укажите ваш рабочий токен Telegram-бота в файле `.env`:
```env
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 3. Запустите бота:
```bash
python main.py
```

---
*Проект полностью автономен и не требует установленного TeleLang.*
"""
        readme_file.write_text(content, encoding="utf-8")
