"""Модуль разрешения конфигурации и секретов (токенов) TeleLang."""

from __future__ import annotations
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from telelang.errors import TeleLangConfigError


class ConfigResolver:
    """Разрешает токены и ключи согласно спецификации TeleLang."""

    @classmethod
    def resolve_bot_token(
        cls,
        cli_token: Optional[str] = None,
        code_token: Optional[str] = None,
        project_dir: Optional[Path] = None,
    ) -> str:
        """Разрешает токен бота с соблюдением приоритета:

        1. CLI аргумент (--token)
        2. Значение в коде .tl (если указано)
        3. Файл .env в папке проекта (BOT_TOKEN)
        4. Переменная окружения ОС (BOT_TOKEN)
        """
        # 1. CLI флаг
        if cli_token and cli_token.strip():
            return cls._validate_format(cli_token.strip())

        # 2. Значение из кода .tl
        if code_token and code_token.strip():
            return cls._validate_format(code_token.strip())

        # 3. Поиск в .env
        if project_dir:
            env_path = project_dir / ".env"
            if env_path.exists():
                load_dotenv(dotenv_path=env_path)
        else:
            load_dotenv()

        token = os.environ.get("BOT_TOKEN")
        if token and token.strip():
            return cls._validate_format(token.strip())

        # 4. Токен не найден — выбрасываем информативную ошибку
        raise TeleLangConfigError(
            message="Не найден токен Telegram-бота.",
            hint=(
                "Укажи токен одним из способов:\n"
                "  1. Создай файл .env в папке проекта:\n"
                "     BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz\n"
                "  2. Либо передай токен через флаг командной строки:\n"
                "     tele run bot.tl --token YOUR_BOT_TOKEN"
            ),
        )

    @classmethod
    def _validate_format(cls, token: str) -> str:
        """Проверяет соответствие формата токена стандарту Telegram Bot API."""
        import re
        if not re.match(r"^\d+:[A-Za-z0-9_-]+$", token):
            raise TeleLangConfigError(
                message=f"Некорректный формат токена Telegram-бота: '{token}'.",
                hint="Токен бота имеет вид '123456789:ABCdefGHIjklMNOpqrsTUVwxyz' (выдаётся @BotFather).",
            )
        return token
