"""Узлы абстрактного синтаксического дерева (AST) TeleLang (Этап 3)."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional
from telelang.errors import SourceSpan


@dataclass(frozen=True)
class ASTNode:
    """Базовый узел AST."""
    span: SourceSpan


# ==========================================
# ВЫРАЖЕНИЯ (Expressions)
# ==========================================

@dataclass(frozen=True)
class Expr(ASTNode):
    """Базовый узел выражения."""
    pass


@dataclass(frozen=True)
class StringLiteral(Expr):
    """Строковый литерал, например "Привет!"."""
    value: str


@dataclass(frozen=True)
class NumberLiteral(Expr):
    """Числовой литерал, например 123 или 3.14."""
    value: int | float


@dataclass(frozen=True)
class BooleanLiteral(Expr):
    """Логический литерал (true / false)."""
    value: bool


@dataclass(frozen=True)
class ListLiteral(Expr):
    """Список значений: ["Python", "Go"]."""
    items: list[Expr] = field(default_factory=list)


@dataclass(frozen=True)
class Identifier(Expr):
    """Идентификатор, например coins или user."""
    name: str


@dataclass(frozen=True)
class MemberAccessExpr(Expr):
    """Доступ к полю объекта: user.coins, message.text, shop.open."""
    target: Expr
    member: str


@dataclass(frozen=True)
class BinaryExpr(Expr):
    """Бинарное выражение: coins > 50, a + b, text contains 'hi'."""
    left: Expr
    op: str
    right: Expr


@dataclass(frozen=True)
class FunctionCallExpr(Expr):
    """Вызов функции: profile(), url("https://...")."""
    func_name: str
    args: list[Expr] = field(default_factory=list)


@dataclass(frozen=True)
class CallApiExpr(Expr):
    """Вызов внешнего API: call weather with { q: "Moscow" }."""
    api_name: str
    params: dict[str, Expr] = field(default_factory=dict)


# ==========================================
# ИНСТРУКЦИИ (Statements)
# ==========================================

@dataclass(frozen=True)
class Stmt(ASTNode):
    """Базовый узел инструкции."""
    pass


@dataclass(frozen=True)
class Block(Stmt):
    """Блок инструкций, заключённый в фигурные скобки { ... }."""
    statements: list[Stmt] = field(default_factory=list)


@dataclass(frozen=True)
class SendStmt(Stmt):
    """Инструкция отправки сообщения: send "..."."""
    message: Expr


@dataclass(frozen=True)
class SendMediaStmt(Stmt):
    """Инструкция отправки медиа: send photo "..." { caption = "..." }."""
    media_type: str  # photo, video, video_note, document, audio, voice, sticker
    file_path: Expr
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VariableAssignStmt(Stmt):
    """Присваивание переменной: coins = 100."""
    name: str
    value: Expr


@dataclass(frozen=True)
class AugAssignStmt(Stmt):
    """Составное присваивание: user.coins += 10."""
    target: Expr
    op: str  # +=, -=
    value: Expr


@dataclass(frozen=True)
class IfStmt(Stmt):
    """Условная конструкция: if condition { ... } else { ... }."""
    condition: Expr
    then_branch: Block
    else_branch: Optional[Block] = None


@dataclass(frozen=True)
class AskStmt(Stmt):
    """Задать вопрос пользователю в FSM: ask "Как тебя зовут?"."""
    prompt: Expr


@dataclass(frozen=True)
class SetStateStmt(Stmt):
    """Переход в состояние FSM: state register_name."""
    state_name: str


@dataclass(frozen=True)
class SaveStmt(Stmt):
    """Сохранение значения в базу: save user.name = message.text."""
    target: Expr
    value: Expr


@dataclass(frozen=True)
class LogStmt(Stmt):
    """Логирование: log "Сообщение" или log_error error."""
    message: Expr
    is_error: bool = False


@dataclass(frozen=True)
class ButtonDef(ASTNode):
    """Определение кнопки: "Купить" -> buy() { style = "primary", icon_emoji = "🔥" }."""
    label: str
    target: Expr
    style: Optional[str] = None
    icon_emoji: Optional[str] = None


@dataclass(frozen=True)
class ButtonsBlock(Stmt):
    """Блок клавиатуры: buttons { ... }."""
    buttons: list[ButtonDef] = field(default_factory=list)


@dataclass(frozen=True)
class ExprStmt(Stmt):
    """Инструкция-выражение, например вызов функции: greet(user.name)."""
    expr: Expr


# ==========================================
# ОБЪЯВЛЕНИЯ ВЕРХНЕГО УРОВНЯ (Declarations)
# ==========================================

@dataclass(frozen=True)
class Declaration(ASTNode):
    """Базовый узел объявления верхнего уровня."""
    pass


@dataclass(frozen=True)
class ImportDecl(Declaration):
    """Импорт модуля: import "utils.tl" [as utils]."""
    path: str
    alias: Optional[str] = None


@dataclass(frozen=True)
class ConfigDecl(Declaration):
    """Объявление параметра на верхнем уровне, например: token = "..."."""
    key: str
    value: Any


@dataclass(frozen=True)
class BotDecl(Declaration):
    """Объявление бота: bot "MyBot" [ { ... } ]."""
    name: str
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class UserbotDecl(Declaration):
    """Объявление юзербота: userbot "MyUserbot" [ { ... } ]."""
    name: str
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DatabaseDecl(Declaration):
    """Объявление таблицы базы данных: database users { coins: number, name: text }."""
    table_name: str
    fields: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RolesDecl(Declaration):
    """Объявление ролей: roles { moderator: ["ban_users"] }."""
    roles: dict[str, list[str]] = field(default_factory=dict)


@dataclass(frozen=True)
class ApiDecl(Declaration):
    """Объявление внешнего API: api weather { url = "...", key = "..." }."""
    name: str
    url: str
    key: Optional[str] = None
    headers: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CommandDecl(Declaration):
    """Объявление команды: command "/start" [only admin] { ... }."""
    command: str
    body: Block
    permission: Optional[str] = None  # None, "admin", "role:moderator", etc.


@dataclass(frozen=True)
class StateDecl(Declaration):
    """Обработчик состояния FSM: state register_name { ... }."""
    name: str
    body: Block


@dataclass(frozen=True)
class OnMessageDecl(Declaration):
    """Обработчик входящих сообщений: on message { ... }."""
    body: Block


@dataclass(frozen=True)
class HookDecl(Declaration):
    """Хук жизненного цикла: before_command, after_command, on_error, on_member_join, on_member_leave."""
    hook_type: str
    body: Block


@dataclass(frozen=True)
class FunctionDecl(Declaration):
    """Объявление пользовательской функции: function hello(name) { ... }."""
    name: str
    body: Block
    params: list[str] = field(default_factory=list)


# ==========================================
# ЭТАП 4: ИНСТРУКЦИИ (Statements)
# ==========================================

@dataclass(frozen=True)
class StreamAiStmt(Stmt):
    """Стриминг ответа ИИ: stream reply from ai openai "{message.text}"."""
    var_name: str
    ai_name: str
    prompt: Expr


@dataclass(frozen=True)
class BroadcastStmt(Stmt):
    """Рассылка сообщения всем пользователям: broadcast "Текст"."""
    message: Expr


@dataclass(frozen=True)
class SendToStmt(Stmt):
    """Отправка сообщения конкретному пользователю: send_to admin "Текст"."""
    target: Expr
    message: Expr


@dataclass(frozen=True)
class SendInvoiceStmt(Stmt):
    """Отправка инвойса/счета: send_invoice { title = "...", price = 100, currency = "XTR" }."""
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReactStmt(Stmt):
    """Установка реакции: react message with "👍"."""
    target: Expr
    emoji: Expr


@dataclass(frozen=True)
class RemoveReactionStmt(Stmt):
    """Снятие реакции: remove_reaction message."""
    target: Expr


@dataclass(frozen=True)
class SendPollStmt(Stmt):
    """Отправка опроса: send poll "..." { options = [...] }."""
    question: Expr
    options: list[Expr] = field(default_factory=list)
    is_quiz: bool = False
    correct_id: int = 0
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SendChecklistStmt(Stmt):
    """Отправка чек-листа (только business bots): send checklist "Title" { task "A" }."""
    title: Expr
    tasks: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SendRichStmt(Stmt):
    """Отправка Rich Message (блоки)."""
    blocks: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class InlineResultDef(ASTNode):
    """Элемент inline-ответа: result article("Заголовок", "Текст") { thumbnail = "..." }."""
    result_type: str
    title: Expr
    content: Expr
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class InlineQueryDecl(Declaration):
    """Хук inline_query { result article(...) }."""
    results: list[InlineResultDef] = field(default_factory=list)


@dataclass(frozen=True)
class AiDecl(Declaration):
    """Объявление ИИ-провайдера: ai openai { key = "...", model = "..." }."""
    name: str
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SchedulerDecl(Declaration):
    """Задача планировщика: every 10 minutes { ... } или every day at "09:00" { ... }."""
    interval_value: int
    interval_unit: str  # minutes, hours, days, day, monday, etc.
    at_time: Optional[str] = None
    body: Block = field(default_factory=lambda: Block(SourceSpan(1, 1, 1, "")))


@dataclass(frozen=True)
class AntispamDecl(Declaration):
    """Конфигурация антиспама: antispam { limit = 5, per = 10 } или antispam off."""
    enabled: bool = True
    limit: int = 5
    per_seconds: int = 10
    action: str = "ignore"


@dataclass(frozen=True)
class LocalesDecl(Declaration):
    """Словарь локализации: locales { ru { ... }, en { ... } }."""
    translations: dict[str, dict[str, str]] = field(default_factory=dict)


@dataclass(frozen=True)
class AnalyticsDecl(Declaration):
    """Конфигурация аналитики: analytics { track_commands = true, track_users = true }."""
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Program(ASTNode):
    """Корневой узел программы TeleLang."""
    declarations: list[Declaration] = field(default_factory=list)
