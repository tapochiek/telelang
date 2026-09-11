"""Модуль исполнения скомпилированного бота (BotRunner)."""

from __future__ import annotations
import asyncio
from pathlib import Path
from typing import Any, Optional
from telelang.compiler import TeleCompiler
from telelang.runtime.config import ConfigResolver


class BotRunner:
    """Запускает скомпилированного бота TeleLang."""

    @classmethod
    def run_file(cls, file_path: str | Path, cli_token: Optional[str] = None) -> None:
        """Компилирует .tl-файл и запускает бота."""
        path = Path(file_path).resolve()
        program, python_code = TeleCompiler.compile_file(path)

        from telelang.parser.ast_nodes import BotDecl, ConfigDecl, UserbotDecl
        is_userbot = any(isinstance(d, UserbotDecl) for d in program.declarations)

        if is_userbot:
            namespace: dict[str, Any] = {
                "__file__": str(path),
                "__name__": "__telelang_runtime__",
            }
            exec(python_code, namespace)
            run_userbot_fn = namespace.get("run_userbot")
            if not callable(run_userbot_fn):
                from telelang.errors import TeleLangRuntimeError
                raise TeleLangRuntimeError("Функция запуска run_userbot не найдена.")
            try:
                asyncio.run(run_userbot_fn())
            except (KeyboardInterrupt, SystemExit):
                pass
            return

        # Извлекаем токен из кода (из bot { token = "..." } или token = "...")
        code_token = None
        for decl in program.declarations:
            if isinstance(decl, BotDecl) and "token" in decl.config:
                code_token = decl.config["token"]
            elif isinstance(decl, ConfigDecl) and decl.key == "token":
                code_token = decl.value

        token = ConfigResolver.resolve_bot_token(
            cli_token=cli_token,
            code_token=code_token,
            project_dir=path.parent,
        )

        # Выполняем сгенерированный код
        namespace: dict[str, Any] = {
            "__file__": str(path),
            "__name__": "__telelang_runtime__",
        }
        exec(python_code, namespace)

        run_bot_fn = namespace.get("run_bot")
        if not callable(run_bot_fn):
            from telelang.errors import TeleLangRuntimeError
            raise TeleLangRuntimeError("Функция запуска run_bot не найдена в скомпилированном коде.")

        try:
            from aiogram.utils.token import TokenValidationError
            try:
                asyncio.run(run_bot_fn(token))
            except TokenValidationError:
                from telelang.errors import TeleLangConfigError
                raise TeleLangConfigError(
                    f"Некорректный формат токена Telegram: '{token}'.",
                    hint="Токен должен иметь вид '123456789:ABCdefGHIjklMNOpqrsTUVwxyz' (выдаётся @BotFather).",
                )
        except (KeyboardInterrupt, SystemExit):
            pass
