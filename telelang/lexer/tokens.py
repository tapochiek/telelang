"""Определения токенов языка TeleLang (Этап 3)."""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any
from telelang.errors import SourceSpan


class TokenType(Enum):
    # Ключевые слова верхнего уровня и режимов
    BOT = auto()
    USERBOT = auto()
    COMMAND = auto()
    ON = auto()
    MESSAGE = auto()
    FUNCTION = auto()
    IMPORT = auto()
    AS = auto()

    # Инструкции и выражения
    SEND = auto()
    IF = auto()
    ELSE = auto()
    BUTTONS = auto()
    URL = auto()
    CONTAINS = auto()
    TRUE = auto()
    FALSE = auto()
    NULL = auto()

    # FSM и Состояния
    STATE = auto()
    ASK = auto()
    SAVE = auto()

    # База данных
    DATABASE = auto()

    # Права и роли
    ONLY = auto()
    ADMIN = auto()
    ROLE = auto()
    ROLES = auto()
    OR = auto()
    AND = auto()
    GRANT = auto()
    REVOKE = auto()
    TO = auto()
    FROM = auto()

    # Медиа-типы
    PHOTO = auto()
    VIDEO = auto()
    VIDEO_NOTE = auto()
    DOCUMENT = auto()
    AUDIO = auto()
    VOICE = auto()
    STICKER = auto()

    # Внешние API
    API = auto()
    CALL = auto()
    WITH = auto()
    HEADER = auto()

    # Хуки и логирование
    BEFORE_COMMAND = auto()
    AFTER_COMMAND = auto()
    ON_ERROR = auto()
    ON_MEMBER_JOIN = auto()
    ON_MEMBER_LEAVE = auto()
    LOG = auto()
    LOG_ERROR = auto()

    # Литералы и идентификаторы
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()

    # Знаки пунктуации и операторы
    LBRACE = auto()       # {
    RBRACE = auto()       # }
    LPAREN = auto()       # (
    RPAREN = auto()       # )
    EQUALS = auto()       # =
    PLUS_EQUALS = auto()  # +=
    MINUS_EQUALS = auto() # -=
    ARROW = auto()        # ->
    DOT = auto()          # .
    COMMA = auto()        # ,
    COLON = auto()        # :

    # Операторы сравнения и логики
    EQEQ = auto()         # ==
    NOT_EQ = auto()       # !=
    LT = auto()           # <
    GT = auto()           # >
    LTE = auto()          # <=
    GTE = auto()          # >=

    # Арифметические операторы
    PLUS = auto()         # +
    MINUS = auto()        # -
    STAR = auto()         # *
    SLASH = auto()        # /

    # Служебные
    EOF = auto()

    # Этап 4: Квадратные скобки
    LBRACKET = auto()     # [
    RBRACKET = auto()     # ]

    # Этап 4: ИИ и стриминг
    AI = auto()
    STREAM = auto()

    # Этап 4: Планировщик
    EVERY = auto()
    AT = auto()
    BROADCAST = auto()
    SEND_TO = auto()

    # Этап 4: Антиспам
    ANTISPAM = auto()
    OFF = auto()
    NO_ANTISPAM = auto()

    # Этап 4: Локализация
    LOCALES = auto()

    # Этап 4: Платежи и социальные фичи
    SEND_INVOICE = auto()
    ON_PAYMENT = auto()
    INLINE_QUERY = auto()
    RESULT = auto()
    CAPTCHA = auto()
    ON_JOIN_REQUEST = auto()
    APPROVE = auto()
    DECLINE = auto()

    # Этап 4: Реакции, Чек-листы, Опросы, Rich messages
    REACT = auto()
    REMOVE_REACTION = auto()
    CHECKLIST = auto()
    TASK = auto()
    ON_CHECKLIST_TASK_DONE = auto()
    POLL = auto()
    QUIZ = auto()
    ON_POLL_ANSWER = auto()
    RICH = auto()

    # Этап 4: Аналитика
    ANALYTICS = auto()


# Словарь всех зарезервированных ключевых слов TeleLang
KEYWORDS: dict[str, TokenType] = {
    "bot": TokenType.BOT,
    "userbot": TokenType.USERBOT,
    "command": TokenType.COMMAND,
    "on": TokenType.ON,
    "message": TokenType.MESSAGE,
    "function": TokenType.FUNCTION,
    "import": TokenType.IMPORT,
    "as": TokenType.AS,
    "send": TokenType.SEND,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "buttons": TokenType.BUTTONS,
    "url": TokenType.URL,
    "contains": TokenType.CONTAINS,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "null": TokenType.NULL,
    "state": TokenType.STATE,
    "ask": TokenType.ASK,
    "save": TokenType.SAVE,
    "database": TokenType.DATABASE,
    "only": TokenType.ONLY,
    "admin": TokenType.ADMIN,
    "role": TokenType.ROLE,
    "roles": TokenType.ROLES,
    "or": TokenType.OR,
    "and": TokenType.AND,
    "grant": TokenType.GRANT,
    "revoke": TokenType.REVOKE,
    "to": TokenType.TO,
    "from": TokenType.FROM,
    "photo": TokenType.PHOTO,
    "video": TokenType.VIDEO,
    "video_note": TokenType.VIDEO_NOTE,
    "document": TokenType.DOCUMENT,
    "audio": TokenType.AUDIO,
    "voice": TokenType.VOICE,
    "sticker": TokenType.STICKER,
    "api": TokenType.API,
    "call": TokenType.CALL,
    "with": TokenType.WITH,
    "header": TokenType.HEADER,
    "before_command": TokenType.BEFORE_COMMAND,
    "after_command": TokenType.AFTER_COMMAND,
    "on_error": TokenType.ON_ERROR,
    "on_member_join": TokenType.ON_MEMBER_JOIN,
    "on_member_leave": TokenType.ON_MEMBER_LEAVE,
    "log": TokenType.LOG,
    "log_error": TokenType.LOG_ERROR,
    # Этап 4
    "ai": TokenType.AI,
    "stream": TokenType.STREAM,
    "every": TokenType.EVERY,
    "at": TokenType.AT,
    "broadcast": TokenType.BROADCAST,
    "send_to": TokenType.SEND_TO,
    "antispam": TokenType.ANTISPAM,
    "off": TokenType.OFF,
    "no_antispam": TokenType.NO_ANTISPAM,
    "locales": TokenType.LOCALES,
    "send_invoice": TokenType.SEND_INVOICE,
    "on_payment": TokenType.ON_PAYMENT,
    "inline_query": TokenType.INLINE_QUERY,
    "result": TokenType.RESULT,
    "captcha": TokenType.CAPTCHA,
    "on_join_request": TokenType.ON_JOIN_REQUEST,
    "approve": TokenType.APPROVE,
    "decline": TokenType.DECLINE,
    "react": TokenType.REACT,
    "remove_reaction": TokenType.REMOVE_REACTION,
    "checklist": TokenType.CHECKLIST,
    "task": TokenType.TASK,
    "on_checklist_task_done": TokenType.ON_CHECKLIST_TASK_DONE,
    "poll": TokenType.POLL,
    "quiz": TokenType.QUIZ,
    "on_poll_answer": TokenType.ON_POLL_ANSWER,
    "rich": TokenType.RICH,
    "analytics": TokenType.ANALYTICS,
}


@dataclass(frozen=True)
class Token:
    """Токен лексического анализатора."""
    type: TokenType
    value: Any
    span: SourceSpan

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, line={self.span.line}, col={self.span.column})"
