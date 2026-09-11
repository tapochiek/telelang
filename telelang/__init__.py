"""TeleLang — предметно-ориентированный язык программирования для Telegram-ботов и юзерботов."""

from telelang.compiler import TeleCompiler
from telelang.errors import TeleLangError

__version__ = "0.1.0-mvp"

__all__ = ["TeleCompiler", "TeleLangError", "__version__"]
