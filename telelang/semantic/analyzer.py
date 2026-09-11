"""Семантический анализатор (Semantic Analyzer) TeleLang (Этап 3)."""

from __future__ import annotations
import re
from typing import Any, Optional
from telelang.errors import TeleLangSemanticError
from telelang.parser.ast_nodes import (
    ApiDecl,
    AskStmt,
    AugAssignStmt,
    Block,
    BotDecl,
    ButtonsBlock,
    CommandDecl,
    ConfigDecl,
    DatabaseDecl,
    FunctionDecl,
    HookDecl,
    IfStmt,
    ImportDecl,
    LogStmt,
    MemberAccessExpr,
    OnMessageDecl,
    Program,
    RolesDecl,
    SaveStmt,
    SendMediaStmt,
    SendStmt,
    SetStateStmt,
    StateDecl,
    Stmt,
    UserbotDecl,
    # Этап 4
    SendChecklistStmt,
    SendRichStmt,
    SendPollStmt,
    SendInvoiceStmt,
    StreamAiStmt,
    BroadcastStmt,
    SendToStmt,
    ReactStmt,
    RemoveReactionStmt,
    InlineQueryDecl,
    AiDecl,
    SchedulerDecl,
    AntispamDecl,
    LocalesDecl,
    AnalyticsDecl,
)


class SemanticAnalyzer:
    """Проверяет семантическую корректность AST-дерева TeleLang."""

    def __init__(self, source_code: str = "", file_path: Optional[str] = None):
        self.source = source_code
        self.file_path = file_path
        self.bot_decl: Optional[BotDecl] = None
        self.userbot_decl: Optional[UserbotDecl] = None
        self.commands: list[CommandDecl] = []
        self.on_messages: list[OnMessageDecl] = []
        self.functions: dict[str, FunctionDecl] = {}
        self.states: dict[str, StateDecl] = {}
        self.databases: dict[str, DatabaseDecl] = {}
        self.apis: dict[str, ApiDecl] = {}
        self.roles: Optional[RolesDecl] = None
        self.hooks: list[HookDecl] = []
        self.imports: list[ImportDecl] = []
        self.configs: dict[str, Any] = {}
        # Этап 4
        self.ais: dict[str, AiDecl] = {}
        self.schedulers: list[SchedulerDecl] = []
        self.antispam: Optional[AntispamDecl] = None
        self.locales: Optional[LocalesDecl] = None
        self.inlines: list[InlineQueryDecl] = []
        self.analytics: Optional[AnalyticsDecl] = None

    def analyze(self, program: Program, is_entrypoint: bool = True) -> None:
        """Выполняет полный семантический анализ программы."""
        # 1. Сбор объявлений верхнего уровня
        for decl in program.declarations:
            if isinstance(decl, ImportDecl):
                self.imports.append(decl)
            elif isinstance(decl, BotDecl):
                self._check_bot_decl(decl)
            elif isinstance(decl, UserbotDecl):
                self._check_userbot_decl(decl)
            elif isinstance(decl, CommandDecl):
                self._check_command_decl(decl)
            elif isinstance(decl, OnMessageDecl):
                self.on_messages.append(decl)
            elif isinstance(decl, FunctionDecl):
                self._check_function_decl(decl)
            elif isinstance(decl, StateDecl):
                self._check_state_decl(decl)
            elif isinstance(decl, DatabaseDecl):
                self.databases[decl.table_name] = decl
            elif isinstance(decl, RolesDecl):
                self.roles = decl
            elif isinstance(decl, ApiDecl):
                self.apis[decl.name] = decl
            elif isinstance(decl, AiDecl):
                self.ais[decl.name] = decl
            elif isinstance(decl, SchedulerDecl):
                self.schedulers.append(decl)
            elif isinstance(decl, AntispamDecl):
                self.antispam = decl
            elif isinstance(decl, LocalesDecl):
                self.locales = decl
            elif isinstance(decl, InlineQueryDecl):
                self.inlines.append(decl)
            elif isinstance(decl, AnalyticsDecl):
                self.analytics = decl
            elif isinstance(decl, HookDecl):
                self.hooks.append(decl)
            elif isinstance(decl, ConfigDecl):
                self._check_config_decl(decl)

        # 2. Проверка наличия точки входа только для основного файла (is_entrypoint=True)
        if is_entrypoint and not self.bot_decl and not self.userbot_decl:
            raise TeleLangSemanticError(
                "В файле не найдено объявление бота ('bot') или юзербота ('userbot').",
                span=program.span,
                source_code=self.source,
                hint='Добавь объявление бота в начале файла, например: bot "MyBot"',
            )

        # 3. Проверка тел обработчиков, функций и состояний
        for cmd in self.commands:
            self._check_block(cmd.body)

        for on_msg in self.on_messages:
            self._check_block(on_msg.body)

        for fn in self.functions.values():
            self._check_block(fn.body)

        for st in self.states.values():
            self._check_block(st.body)

        for hk in self.hooks:
            self._check_block(hk.body)

    def _check_bot_decl(self, decl: BotDecl) -> None:
        if self.userbot_decl:
            raise TeleLangSemanticError(
                "Файл не может одновременно содержать объявление и 'bot', и 'userbot'.",
                span=decl.span,
                source_code=self.source,
                hint="Используй либо режим 'bot' (Telegram Bot API), либо 'userbot' (MTProto), но не оба вместе.",
            )

        if self.bot_decl:
            raise TeleLangSemanticError(
                f"Повторное объявление бота '{decl.name}'. В файле может быть объявлен только один бот.",
                span=decl.span,
                source_code=self.source,
                hint="Удали дублирующее объявление 'bot'.",
            )

        mode = decl.config.get("mode", "polling")
        if mode not in ("polling", "webhook"):
            raise TeleLangSemanticError(
                f"Недопустимый режим работы бота: '{mode}'.",
                span=decl.span,
                source_code=self.source,
                hint="Допустимые режимы: 'polling' или 'webhook'.",
            )

        if mode == "webhook" and "webhook_url" not in decl.config:
            raise TeleLangSemanticError(
                "Для режима 'webhook' необходимо указать 'webhook_url'.",
                span=decl.span,
                source_code=self.source,
                hint='Укажи: webhook_url = "https://example.com/telegram/webhook"',
            )

        self.bot_decl = decl

    def _check_userbot_decl(self, decl: UserbotDecl) -> None:
        if self.bot_decl:
            raise TeleLangSemanticError(
                "Файл не может одновременно содержать объявление и 'bot', и 'userbot'.",
                span=decl.span,
                source_code=self.source,
                hint="Используй либо режим 'bot' (Telegram Bot API), либо 'userbot' (MTProto), но не оба вместе.",
            )

        if self.userbot_decl:
            raise TeleLangSemanticError(
                f"Повторное объявление юзербота '{decl.name}'. В файле может быть объявлен только один юзербот.",
                span=decl.span,
                source_code=self.source,
                hint="Удали дублирующее объявление 'userbot'.",
            )

        if "mode" in decl.config:
            raise TeleLangSemanticError(
                "Параметр 'mode' не применим к юзерботу. Юзербот всегда работает через постоянное MTProto-соединение.",
                span=decl.span,
                source_code=self.source,
                hint="Удали строку 'mode = ...' из блока userbot.",
            )

        self.userbot_decl = decl

    def _check_command_decl(self, decl: CommandDecl) -> None:
        if not decl.command.startswith("/"):
            clean_cmd = decl.command.lstrip("/")
            raise TeleLangSemanticError(
                f"Имя команды '{decl.command}' должно начинаться с символа '/'.",
                span=decl.span,
                source_code=self.source,
                hint=f'Исправь на: command "/{clean_cmd}"',
            )

        self.commands.append(decl)

    def _check_function_decl(self, decl: FunctionDecl) -> None:
        if decl.name in self.functions:
            raise TeleLangSemanticError(
                f"Повторное объявление функции '{decl.name}'.",
                span=decl.span,
                source_code=self.source,
                hint=f"Выбери уникальное имя для функции '{decl.name}'.",
            )

        seen_params = set()
        for p in decl.params:
            if p in seen_params:
                raise TeleLangSemanticError(
                    f"Дублирующийся параметр '{p}' в функции '{decl.name}'.",
                    span=decl.span,
                    source_code=self.source,
                )
            seen_params.add(p)

        self.functions[decl.name] = decl

    def _check_state_decl(self, decl: StateDecl) -> None:
        if decl.name in self.states:
            raise TeleLangSemanticError(
                f"Повторное объявление состояния '{decl.name}'.",
                span=decl.span,
                source_code=self.source,
            )
        self.states[decl.name] = decl

    def _check_config_decl(self, decl: ConfigDecl) -> None:
        if decl.key == "token":
            if isinstance(decl.value, str):
                if not re.match(r"^\d+:[A-Za-z0-9_-]+$", decl.value):
                    raise TeleLangSemanticError(
                        f"Некорректный формат токена Telegram-бота: '{decl.value}'.",
                        span=decl.span,
                        source_code=self.source,
                        hint="Токен бота имеет вид '123456789:ABCdefGHIjklMNOpqrsTUVwxyz' (выдаётся @BotFather).",
                    )
        self.configs[decl.key] = decl.value

    def _check_block(self, block: Block) -> None:
        for stmt in block.statements:
            self._check_statement(stmt)

    def _check_statement(self, stmt: Stmt) -> None:
        if isinstance(stmt, ButtonsBlock):
            if self.userbot_decl:
                raise TeleLangSemanticError(
                    "Блок 'buttons' недоступен в режиме 'userbot'.",
                    span=stmt.span,
                    source_code=self.source,
                    hint="Кнопки интерфейса поддерживаются только Telegram Bot API (режим 'bot').",
                )

        elif isinstance(stmt, SendChecklistStmt):
            if self.userbot_decl:
                raise TeleLangSemanticError(
                    "Чек-листы ('send checklist') недоступны в режиме 'userbot'.",
                    span=stmt.span,
                    source_code=self.source,
                    hint="Чек-листы поддерживаются только через Bot API для подключённых Business-ботов.",
                )
            # Проверка business_connection_id у бота
            if self.bot_decl and "business_connection_id" not in self.bot_decl.config:
                raise TeleLangSemanticError(
                    "Чек-листы доступны только для ботов, подключённых как Business-бот к Premium-аккаунту.",
                    span=stmt.span,
                    source_code=self.source,
                    hint="Добавь 'business_connection_id = \"...\"' в блок bot { ... }.",
                )

        elif isinstance(stmt, SendInvoiceStmt):
            if self.userbot_decl:
                raise TeleLangSemanticError(
                    "Инвойсы ('send_invoice') недоступны в режиме 'userbot'.",
                    span=stmt.span,
                    source_code=self.source,
                    hint="Платежи поддерживаются только в режиме 'bot' через Telegram Bot API.",
                )

        elif isinstance(stmt, IfStmt):
            self._check_block(stmt.then_branch)
            if stmt.else_branch:
                self._check_block(stmt.else_branch)
