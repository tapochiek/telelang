"""Синтаксический анализатор (Parser) TeleLang (Этап 3)."""

from __future__ import annotations
from typing import Any, Optional
from telelang.errors import SourceSpan, TeleLangSyntaxError
from telelang.lexer.tokens import Token, TokenType
from telelang.parser.ast_nodes import (
    ApiDecl,
    AskStmt,
    AugAssignStmt,
    BinaryExpr,
    Block,
    BooleanLiteral,
    BotDecl,
    ButtonDef,
    ButtonsBlock,
    CallApiExpr,
    CommandDecl,
    ConfigDecl,
    DatabaseDecl,
    Declaration,
    Expr,
    ExprStmt,
    FunctionCallExpr,
    FunctionDecl,
    HookDecl,
    Identifier,
    IfStmt,
    ImportDecl,
    LogStmt,
    MemberAccessExpr,
    NumberLiteral,
    OnMessageDecl,
    Program,
    RolesDecl,
    SaveStmt,
    SendMediaStmt,
    SendStmt,
    SetStateStmt,
    StateDecl,
    Stmt,
    StringLiteral,
    UserbotDecl,
    VariableAssignStmt,
    # Этап 4
    ListLiteral,
    StreamAiStmt,
    BroadcastStmt,
    SendToStmt,
    SendInvoiceStmt,
    ReactStmt,
    RemoveReactionStmt,
    SendPollStmt,
    SendChecklistStmt,
    SendRichStmt,
    InlineResultDef,
    InlineQueryDecl,
    AiDecl,
    SchedulerDecl,
    AntispamDecl,
    LocalesDecl,
    AnalyticsDecl,
)

MEDIA_TOKENS = {
    TokenType.PHOTO: "photo",
    TokenType.VIDEO: "video",
    TokenType.VIDEO_NOTE: "video_note",
    TokenType.DOCUMENT: "document",
    TokenType.AUDIO: "audio",
    TokenType.VOICE: "voice",
    TokenType.STICKER: "sticker",
}

HOOK_TOKENS = {
    TokenType.BEFORE_COMMAND: "before_command",
    TokenType.AFTER_COMMAND: "after_command",
    TokenType.ON_ERROR: "on_error",
    TokenType.ON_MEMBER_JOIN: "on_member_join",
    TokenType.ON_MEMBER_LEAVE: "on_member_leave",
}


class Parser:
    """Парсер TeleLang методом рекурсивного спуска."""

    def __init__(self, tokens: list[Token], source_code: str = "", file_path: Optional[str] = None):
        self.tokens = tokens
        self.source = source_code
        self.file_path = file_path
        self.pos = 0

    def _current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]

    def _peek(self, offset: int = 1) -> Token:
        p = self.pos + offset
        if p < len(self.tokens):
            return self.tokens[p]
        return self.tokens[-1]

    def _match(self, *types: TokenType) -> bool:
        if self._current().type in types:
            self.pos += 1
            return True
        return False

    def _expect(self, token_type: TokenType, error_message: str, hint: Optional[str] = None) -> Token:
        tok = self._current()
        if tok.type != token_type:
            raise TeleLangSyntaxError(
                error_message,
                span=tok.span,
                source_code=self.source,
                hint=hint,
            )
        self.pos += 1
        return tok

    def parse(self) -> Program:
        """Парсит весь входной поток токенов в Program AST."""
        declarations: list[Declaration] = []
        start_span = self._current().span

        while self._current().type != TokenType.EOF:
            decl = self._parse_declaration()
            if decl:
                declarations.append(decl)

        end_span = self._current().span
        prog_span = SourceSpan(
            start_span.line,
            start_span.column,
            max(1, end_span.column - start_span.column if end_span.line == start_span.line else 1),
            self.file_path,
        )
        return Program(declarations=declarations, span=prog_span)

    # ==========================================
    # ОБЪЯВЛЕНИЯ (Declarations)
    # ==========================================

    def _parse_declaration(self) -> Declaration:
        tok = self._current()

        if tok.type == TokenType.IMPORT:
            return self._parse_import_decl()

        if tok.type == TokenType.BOT:
            return self._parse_bot_decl()

        if tok.type == TokenType.USERBOT:
            return self._parse_userbot_decl()

        if tok.type == TokenType.COMMAND:
            return self._parse_command_decl()

        if tok.type == TokenType.ON:
            return self._parse_on_decl()

        if tok.type == TokenType.FUNCTION:
            return self._parse_function_decl()

        if tok.type == TokenType.STATE:
            return self._parse_state_decl()

        if tok.type == TokenType.DATABASE:
            return self._parse_database_decl()

        if tok.type == TokenType.ROLES:
            return self._parse_roles_decl()

        if tok.type == TokenType.API:
            return self._parse_api_decl()

        if tok.type == TokenType.AI:
            return self._parse_ai_decl()

        if tok.type == TokenType.EVERY:
            return self._parse_scheduler_decl()

        if tok.type == TokenType.ANTISPAM:
            return self._parse_antispam_decl()

        if tok.type == TokenType.LOCALES:
            return self._parse_locales_decl()

        if tok.type == TokenType.INLINE_QUERY:
            return self._parse_inline_query_decl()

        if tok.type == TokenType.ANALYTICS:
            return self._parse_analytics_decl()

        if tok.type in (
            TokenType.ON_PAYMENT,
            TokenType.ON_JOIN_REQUEST,
            TokenType.ON_CHECKLIST_TASK_DONE,
            TokenType.ON_POLL_ANSWER,
        ):
            return self._parse_special_hook_decl()

        if tok.type in HOOK_TOKENS:
            return self._parse_hook_decl()

        if tok.type == TokenType.IDENTIFIER:
            return self._parse_top_level_assignment()

        raise TeleLangSyntaxError(
            f"Неожиданная инструкция на верхнем уровне: '{tok.value}'.",
            span=tok.span,
            source_code=self.source,
            hint="На верхнем уровне поддерживаются: bot, userbot, command, on message, function, state, database, roles, api, ai, every, antispam, locales, inline_query, analytics.",
        )

    def _parse_import_decl(self) -> ImportDecl:
        imp_tok = self._expect(TokenType.IMPORT, "Ожидалось ключевое слово 'import'.")
        path_tok = self._expect(TokenType.STRING, "Ожидался путь к импортируемому файлу в кавычках.", hint='Пример: import "utils.tl"')
        alias: Optional[str] = None
        if self._match(TokenType.AS):
            alias_tok = self._expect(TokenType.IDENTIFIER, "Ожидался псевдоним после 'as'.", hint='Пример: import "shop.tl" as shop')
            alias = alias_tok.value

        span = SourceSpan(imp_tok.span.line, imp_tok.span.column, len(path_tok.value) + 8, self.file_path)
        return ImportDecl(path=path_tok.value, alias=alias, span=span)

    def _parse_bot_decl(self) -> BotDecl:
        start_tok = self._expect(TokenType.BOT, "Ожидалось ключевое слово 'bot'.")
        name_tok = self._expect(
            TokenType.STRING,
            "После ключевого слова 'bot' ожидается имя бота в кавычках.",
            hint='Пример: bot "MyBot"',
        )
        config: dict[str, Any] = {}
        if self._current().type == TokenType.LBRACE:
            config = self._parse_config_block()

        span = SourceSpan(start_tok.span.line, start_tok.span.column, len(name_tok.value) + 5, self.file_path)
        return BotDecl(name=name_tok.value, config=config, span=span)

    def _parse_userbot_decl(self) -> UserbotDecl:
        start_tok = self._expect(TokenType.USERBOT, "Ожидалось ключевое слово 'userbot'.")
        name_tok = self._expect(
            TokenType.STRING,
            "После ключевого слова 'userbot' ожидается имя юзербота в кавычках.",
            hint='Пример: userbot "MyUserbot"',
        )
        config: dict[str, Any] = {}
        if self._current().type == TokenType.LBRACE:
            config = self._parse_config_block()

        span = SourceSpan(start_tok.span.line, start_tok.span.column, len(name_tok.value) + 9, self.file_path)
        return UserbotDecl(name=name_tok.value, config=config, span=span)

    def _parse_config_block(self) -> dict[str, Any]:
        self._expect(TokenType.LBRACE, "Ожидался символ '{' для начала блока конфигурации.")
        config: dict[str, Any] = {}

        while self._current().type != TokenType.RBRACE and self._current().type != TokenType.EOF:
            key_tok = self._expect(
                TokenType.IDENTIFIER,
                "В блоке конфигурации ожидается имя параметра.",
                hint='Пример: mode = "polling"',
            )
            self._expect(TokenType.EQUALS, f"Ожидался символ '=' после имени параметра '{key_tok.value}'.")
            val_tok = self._current()

            if val_tok.type in (TokenType.STRING, TokenType.NUMBER, TokenType.IDENTIFIER):
                self.pos += 1
                val = val_tok.value
                # Если после числа сразу идет 's', 'm', 'h' (например 10s, 60s)
                if val_tok.type == TokenType.NUMBER and self._current().type == TokenType.IDENTIFIER:
                    suffix = self._current().value
                    if suffix in ("s", "m", "h", "min", "sec"):
                        val = f"{val}{suffix}"
                        self.pos += 1
                config[key_tok.value] = val
            else:
                raise TeleLangSyntaxError(
                    f"Недопустимое значение '{val_tok.value}' для параметра '{key_tok.value}'.",
                    span=val_tok.span,
                    source_code=self.source,
                    hint="Параметры могут принимать строки или числа.",
                )

        self._expect(TokenType.RBRACE, "Ожидался символ '}' для закрытия блока конфигурации.")
        return config

    def _parse_command_decl(self) -> CommandDecl:
        cmd_tok = self._expect(TokenType.COMMAND, "Ожидалось ключевое слово 'command'.")
        name_tok = self._expect(
            TokenType.STRING,
            "После ключевого слова 'command' ожидается имя команды в кавычках.",
            hint='Пример: command "/start" { ... }',
        )

        permission: Optional[str] = None
        if self._match(TokenType.ONLY):
            if self._match(TokenType.ADMIN):
                permission = "admin"
            elif self._match(TokenType.ROLE):
                role_name_tok = self._expect(TokenType.STRING, "Ожидалось имя роли в кавычках.")
                permission = f"role:{role_name_tok.value}"
                if self._match(TokenType.OR):
                    self._expect(TokenType.ADMIN, "Ожидалось 'admin' после 'or'.")
                    permission += " or admin"

        body = self._parse_block()
        span = SourceSpan(cmd_tok.span.line, cmd_tok.span.column, len(name_tok.value) + 9, self.file_path)
        return CommandDecl(command=name_tok.value, body=body, permission=permission, span=span)

    def _parse_on_decl(self) -> OnMessageDecl:
        on_tok = self._expect(TokenType.ON, "Ожидалось ключевое слово 'on'.")
        self._expect(
            TokenType.MESSAGE,
            "После 'on' ожидается тип события, например: on message { ... }.",
            hint="Пример: on message { ... }",
        )
        body = self._parse_block()
        span = SourceSpan(on_tok.span.line, on_tok.span.column, 10, self.file_path)
        return OnMessageDecl(body=body, span=span)

    def _parse_function_decl(self) -> FunctionDecl:
        fn_tok = self._expect(TokenType.FUNCTION, "Ожидалось ключевое слово 'function'.")
        name_tok = self._expect(TokenType.IDENTIFIER, "Ожидалось имя функции.", hint="Пример: function greet(name) { ... }")
        self._expect(TokenType.LPAREN, "Ожидалась открывающая скобка '(' после имени функции.")

        params: list[str] = []
        if self._current().type != TokenType.RPAREN:
            p_tok = self._expect(TokenType.IDENTIFIER, "Ожидалось имя параметра функции.")
            params.append(p_tok.value)
            while self._match(TokenType.COMMA):
                p_tok = self._expect(TokenType.IDENTIFIER, "Ожидалось имя параметра функции после запятой.")
                params.append(p_tok.value)

        self._expect(TokenType.RPAREN, "Ожидалась закрывающая скобка ')' после списка параметров.")
        body = self._parse_block()
        span = SourceSpan(fn_tok.span.line, fn_tok.span.column, len(name_tok.value) + 9, self.file_path)
        return FunctionDecl(name=name_tok.value, body=body, params=params, span=span)

    def _parse_state_decl(self) -> StateDecl:
        state_tok = self._expect(TokenType.STATE, "Ожидалось ключевое слово 'state'.")
        name_tok = self._expect(TokenType.IDENTIFIER, "Ожидалось имя состояния FSM.", hint="Пример: state register_name { ... }")
        body = self._parse_block()
        span = SourceSpan(state_tok.span.line, state_tok.span.column, len(name_tok.value) + 7, self.file_path)
        return StateDecl(name=name_tok.value, body=body, span=span)

    def _parse_database_decl(self) -> DatabaseDecl:
        db_tok = self._expect(TokenType.DATABASE, "Ожидалось ключевое слово 'database'.")
        table_tok = self._expect(TokenType.IDENTIFIER, "Ожидалось имя таблицы базы данных.", hint="Пример: database users { coins: number }")
        self._expect(TokenType.LBRACE, "Ожидался символ '{' для начала схемы базы данных.")
        fields: dict[str, str] = {}

        while self._current().type != TokenType.RBRACE and self._current().type != TokenType.EOF:
            field_name_tok = self._expect(TokenType.IDENTIFIER, "Ожидалось имя поля таблицы.")
            self._expect(TokenType.COLON, "Ожидался символ ':' после имени поля.")
            type_tok = self._expect(TokenType.IDENTIFIER, "Ожидался тип поля (number или text).")
            fields[field_name_tok.value] = type_tok.value

        self._expect(TokenType.RBRACE, "Ожидался символ '}' для закрытия схемы базы данных.")
        span = SourceSpan(db_tok.span.line, db_tok.span.column, len(table_tok.value) + 10, self.file_path)
        return DatabaseDecl(table_name=table_tok.value, fields=fields, span=span)

    def _parse_roles_decl(self) -> RolesDecl:
        roles_tok = self._expect(TokenType.ROLES, "Ожидалось ключевое слово 'roles'.")
        self._expect(TokenType.LBRACE, "Ожидался символ '{' для начала блока ролей.")
        roles: dict[str, list[str]] = {}

        while self._current().type != TokenType.RBRACE and self._current().type != TokenType.EOF:
            role_name_tok = self._expect(TokenType.IDENTIFIER, "Ожидалось имя роли.")
            self._expect(TokenType.COLON, "Ожидался символ ':' после имени роли.")
            # Список разрешений в квадратных скобках или строках
            perms: list[str] = []
            if self._current().value == "[" or self._current().type == TokenType.STRING:
                # Читаем строки
                if self._current().value == "[":
                    self.pos += 1
                    while self._current().type != TokenType.EOF and self._current().value != "]":
                        if self._current().type == TokenType.STRING:
                            perms.append(self._current().value)
                            self.pos += 1
                        elif self._current().type == TokenType.COMMA:
                            self.pos += 1
                        else:
                            self.pos += 1
                    if self._current().value == "]":
                        self.pos += 1
            roles[role_name_tok.value] = perms

        self._expect(TokenType.RBRACE, "Ожидался символ '}' для закрытия блока ролей.")
        span = SourceSpan(roles_tok.span.line, roles_tok.span.column, 6, self.file_path)
        return RolesDecl(roles=roles, span=span)

    def _parse_api_decl(self) -> ApiDecl:
        api_tok = self._expect(TokenType.API, "Ожидалось ключевое слово 'api'.")
        name_tok = self._expect(TokenType.IDENTIFIER, "Ожидалось имя внешнего API.", hint="Пример: api weather { ... }")
        self._expect(TokenType.LBRACE, "Ожидался символ '{' для начала блока api.")
        url: str = ""
        key: Optional[str] = None
        headers: dict[str, str] = {}

        while self._current().type != TokenType.RBRACE and self._current().type != TokenType.EOF:
            if self._current().type == TokenType.HEADER:
                self.pos += 1
                h_name_tok = self._expect(TokenType.STRING, "Ожидалось имя заголовка в кавычках.")
                self._expect(TokenType.EQUALS, "Ожидался '='.")
                h_val_tok = self._expect(TokenType.STRING, "Ожидалось значение заголовка в кавычках.")
                headers[h_name_tok.value] = h_val_tok.value
            elif self._current().type == TokenType.IDENTIFIER:
                prop = self._current().value
                self.pos += 1
                self._expect(TokenType.EQUALS, "Ожидался '='.")
                val_tok = self._current()
                self.pos += 1
                if prop == "url":
                    url = val_tok.value
                elif prop == "key":
                    key = val_tok.value
            else:
                self.pos += 1

        self._expect(TokenType.RBRACE, "Ожидался символ '}' для закрытия блока api.")
        span = SourceSpan(api_tok.span.line, api_tok.span.column, len(name_tok.value) + 5, self.file_path)
        return ApiDecl(name=name_tok.value, url=url, key=key, headers=headers, span=span)

    def _parse_ai_decl(self) -> AiDecl:
        ai_tok = self._expect(TokenType.AI, "Ожидалось ключевое слово 'ai'.")
        name_tok = self._expect(TokenType.IDENTIFIER, "Ожидалось имя ИИ-провайдера.", hint="Пример: ai openai { ... }")
        config = self._parse_config_block() if self._current().type == TokenType.LBRACE else {}
        span = SourceSpan(ai_tok.span.line, ai_tok.span.column, len(name_tok.value) + 4, self.file_path)
        return AiDecl(name=name_tok.value, config=config, span=span)

    def _parse_scheduler_decl(self) -> SchedulerDecl:
        every_tok = self._expect(TokenType.EVERY, "Ожидалось ключевое слово 'every'.")
        val = 1
        unit = "minutes"
        if self._current().type == TokenType.NUMBER:
            val = int(self._current().value)
            self.pos += 1
            unit_tok = self._expect(TokenType.IDENTIFIER, "Ожидалась единица измерения времени (minutes, hours, seconds).")
            unit = unit_tok.value
        elif self._current().type == TokenType.IDENTIFIER:
            unit = self._current().value
            self.pos += 1

        at_time = None
        if self._match(TokenType.AT):
            at_tok = self._expect(TokenType.STRING, "Ожидалось время в формате 'HH:MM'.", hint='Пример: at "09:00"')
            at_time = at_tok.value

        body = self._parse_block()
        span = SourceSpan(every_tok.span.line, every_tok.span.column, 6, self.file_path)
        return SchedulerDecl(interval_value=val, interval_unit=unit, at_time=at_time, body=body, span=span)

    def _parse_antispam_decl(self) -> AntispamDecl:
        anti_tok = self._expect(TokenType.ANTISPAM, "Ожидалось ключевое слово 'antispam'.")
        if self._match(TokenType.OFF):
            span = SourceSpan(anti_tok.span.line, anti_tok.span.column, 12, self.file_path)
            return AntispamDecl(enabled=False, span=span)

        config = self._parse_config_block() if self._current().type == TokenType.LBRACE else {}
        limit = int(config.get("limit", 5))
        per_raw = str(config.get("per", "10s")).rstrip("s")
        per_sec = int(per_raw) if per_raw.isdigit() else 10
        action = str(config.get("action", "ignore"))
        span = SourceSpan(anti_tok.span.line, anti_tok.span.column, 8, self.file_path)
        return AntispamDecl(enabled=True, limit=limit, per_seconds=per_sec, action=action, span=span)

    def _parse_locales_decl(self) -> LocalesDecl:
        loc_tok = self._expect(TokenType.LOCALES, "Ожидалось ключевое слово 'locales'.")
        self._expect(TokenType.LBRACE, "Ожидался символ '{' для начала блока locales.")
        translations: dict[str, dict[str, str]] = {}

        while self._current().type != TokenType.RBRACE and self._current().type != TokenType.EOF:
            lang_tok = self._expect(TokenType.IDENTIFIER, "Ожидался код языка (например ru, en).")
            self._expect(TokenType.LBRACE, f"Ожидался символ '{{' для словаря языка '{lang_tok.value}'.")
            lang_dict: dict[str, str] = {}
            while self._current().type != TokenType.RBRACE and self._current().type != TokenType.EOF:
                k_tok = self._expect(TokenType.IDENTIFIER, "Ожидался ключ перевода.")
                self._expect(TokenType.EQUALS, "Ожидался '='.")
                v_tok = self._expect(TokenType.STRING, "Ожидалась строка перевода в кавычках.")
                lang_dict[k_tok.value] = v_tok.value
            self._expect(TokenType.RBRACE, "Ожидался символ '}' для закрытия словаря языка.")
            translations[lang_tok.value] = lang_dict

        self._expect(TokenType.RBRACE, "Ожидался символ '}' для закрытия блока locales.")
        span = SourceSpan(loc_tok.span.line, loc_tok.span.column, 7, self.file_path)
        return LocalesDecl(translations=translations, span=span)

    def _parse_inline_query_decl(self) -> InlineQueryDecl:
        iq_tok = self._expect(TokenType.INLINE_QUERY, "Ожидалось ключевое слово 'inline_query'.")
        self._expect(TokenType.LBRACE, "Ожидался символ '{' для начала блока inline_query.")
        results: list[InlineResultDef] = []

        while self._current().type != TokenType.RBRACE and self._current().type != TokenType.EOF:
            self._expect(TokenType.RESULT, "Ожидалось ключевое слово 'result'.")
            res_type_tok = self._expect(TokenType.IDENTIFIER, "Ожидался тип результата (например article).")
            self._expect(TokenType.LPAREN, "Ожидалась '(' после типа результата.")
            title_expr = self._parse_expression()
            self._expect(TokenType.COMMA, "Ожидалась запятая между заголовком и текстом.")
            content_expr = self._parse_expression()
            self._expect(TokenType.RPAREN, "Ожидалась ')' после параметров результата.")

            options = {}
            if self._current().type == TokenType.LBRACE:
                options = self._parse_config_block()

            res_span = SourceSpan(res_type_tok.span.line, res_type_tok.span.column, len(res_type_tok.value), self.file_path)
            results.append(InlineResultDef(result_type=res_type_tok.value, title=title_expr, content=content_expr, options=options, span=res_span))

        self._expect(TokenType.RBRACE, "Ожидался символ '}' для закрытия блока inline_query.")
        span = SourceSpan(iq_tok.span.line, iq_tok.span.column, 12, self.file_path)
        return InlineQueryDecl(results=results, span=span)

    def _parse_analytics_decl(self) -> AnalyticsDecl:
        an_tok = self._expect(TokenType.ANALYTICS, "Ожидалось ключевое слово 'analytics'.")
        config = self._parse_config_block() if self._current().type == TokenType.LBRACE else {}
        span = SourceSpan(an_tok.span.line, an_tok.span.column, 9, self.file_path)
        return AnalyticsDecl(config=config, span=span)

    def _parse_special_hook_decl(self) -> HookDecl:
        hook_tok = self._current()
        self.pos += 1
        hook_name_map = {
            TokenType.ON_PAYMENT: "on_payment",
            TokenType.ON_JOIN_REQUEST: "on_join_request",
            TokenType.ON_CHECKLIST_TASK_DONE: "on_checklist_task_done",
            TokenType.ON_POLL_ANSWER: "on_poll_answer",
        }
        hook_type = hook_name_map.get(hook_tok.type, "on_unknown")
        body = self._parse_block()
        span = SourceSpan(hook_tok.span.line, hook_tok.span.column, len(hook_type), self.file_path)
        return HookDecl(hook_type=hook_type, body=body, span=span)

    def _parse_hook_decl(self) -> HookDecl:
        hook_tok = self._current()
        self.pos += 1
        hook_type = HOOK_TOKENS[hook_tok.type]
        body = self._parse_block()
        span = SourceSpan(hook_tok.span.line, hook_tok.span.column, len(hook_type), self.file_path)
        return HookDecl(hook_type=hook_type, body=body, span=span)

    def _parse_top_level_assignment(self) -> ConfigDecl:
        key_tok = self._expect(TokenType.IDENTIFIER, "Ожидалось имя параметра.")
        self._expect(
            TokenType.EQUALS,
            f"Ожидался символ '=' после '{key_tok.value}'.",
            hint=f'Пример: {key_tok.value} = "..."',
        )
        val_tok = self._current()
        if val_tok.type in (TokenType.STRING, TokenType.NUMBER, TokenType.IDENTIFIER):
            self.pos += 1
            span = SourceSpan(key_tok.span.line, key_tok.span.column, len(key_tok.value), self.file_path)
            return ConfigDecl(key=key_tok.value, value=val_tok.value, span=span)

        raise TeleLangSyntaxError(
            f"Недопустимое значение '{val_tok.value}' для параметра '{key_tok.value}'.",
            span=val_tok.span,
            source_code=self.source,
            hint="Параметры могут принимать строки или числа.",
        )

    # ==========================================
    # ИНСТРУКЦИИ (Statements)
    # ==========================================

    def _parse_block(self) -> Block:
        open_brace = self._expect(TokenType.LBRACE, "Ожидался символ '{' для начала блока кода.")
        statements: list[Stmt] = []

        while self._current().type != TokenType.RBRACE and self._current().type != TokenType.EOF:
            stmt = self._parse_statement()
            if stmt:
                statements.append(stmt)

        self._expect(
            TokenType.RBRACE,
            "Незакрытый блок: ожидался символ '}'.",
            hint="Проверь, чтобы у каждого открывающего '{' был соответствующий закрывающий '}'.",
        )

        span = SourceSpan(open_brace.span.line, open_brace.span.column, 1, self.file_path)
        return Block(statements=statements, span=span)

    def _parse_statement(self) -> Stmt:
        tok = self._current()

        if tok.type == TokenType.SEND:
            return self._parse_send_stmt()

        if tok.type == TokenType.IF:
            return self._parse_if_stmt()

        if tok.type == TokenType.BUTTONS:
            return self._parse_buttons_block()

        if tok.type == TokenType.ASK:
            return self._parse_ask_stmt()

        if tok.type == TokenType.STATE:
            return self._parse_set_state_stmt()

        if tok.type == TokenType.SAVE:
            return self._parse_save_stmt()

        if tok.type in (TokenType.LOG, TokenType.LOG_ERROR):
            return self._parse_log_stmt()

        # Этап 4
        if tok.type == TokenType.STREAM:
            return self._parse_stream_ai_stmt()

        if tok.type == TokenType.BROADCAST:
            return self._parse_broadcast_stmt()

        if tok.type == TokenType.SEND_TO:
            return self._parse_send_to_stmt()

        if tok.type == TokenType.SEND_INVOICE:
            return self._parse_send_invoice_stmt()

        if tok.type == TokenType.REACT:
            return self._parse_react_stmt()

        if tok.type == TokenType.REMOVE_REACTION:
            return self._parse_remove_reaction_stmt()

        if tok.type in (TokenType.APPROVE, TokenType.DECLINE):
            self.pos += 1
            action_name = tok.value
            return ExprStmt(expr=Identifier(name=action_name, span=tok.span), span=tok.span)

        if tok.type in (TokenType.IDENTIFIER, TokenType.RESULT):
            # Проверяем на обычное или составное присваивание (user.coins += 10, result = ...)
            expr = self._parse_expression()
            if self._match(TokenType.EQUALS):
                val_expr = self._parse_expression()
                name = expr.name if isinstance(expr, Identifier) else str(expr)
                return VariableAssignStmt(name=name, value=val_expr, span=expr.span)
            elif self._match(TokenType.PLUS_EQUALS):
                val_expr = self._parse_expression()
                return AugAssignStmt(target=expr, op="+=", value=val_expr, span=expr.span)
            elif self._match(TokenType.MINUS_EQUALS):
                val_expr = self._parse_expression()
                return AugAssignStmt(target=expr, op="-=", value=val_expr, span=expr.span)
            else:
                return ExprStmt(expr=expr, span=expr.span)

        raise TeleLangSyntaxError(
            f"Неожиданная инструкция: '{tok.value}'.",
            span=tok.span,
            source_code=self.source,
            hint="Поддерживаются: send, if, buttons, ask, state, save, log или вызовы функций.",
        )

    def _parse_send_stmt(self) -> Stmt:
        send_tok = self._expect(TokenType.SEND, "Ожидалась инструкция 'send'.")
        next_tok = self._current()

        # Проверка на опрос: send poll "..." { options = [...] }
        if next_tok.type in (TokenType.POLL, TokenType.QUIZ):
            is_quiz = next_tok.type == TokenType.QUIZ
            self.pos += 1
            question_expr = self._parse_expression()
            self._expect(TokenType.LBRACE, "Ожидался '{' для параметров опроса/квиза.")
            options_list = []
            correct_id = 0
            extra_opts = {}
            while self._current().type != TokenType.RBRACE and self._current().type != TokenType.EOF:
                if self._current().type == TokenType.IDENTIFIER and self._current().value == "options":
                    self.pos += 1
                    self._expect(TokenType.EQUALS, "Ожидался '='.")
                    opts_expr = self._parse_expression()
                    if isinstance(opts_expr, ListLiteral):
                        options_list = opts_expr.items
                elif self._current().type == TokenType.IDENTIFIER and self._current().value == "correct":
                    self.pos += 1
                    self._expect(TokenType.EQUALS, "Ожидался '='.")
                    c_tok = self._expect(TokenType.NUMBER, "Ожидался номер правильного ответа.")
                    correct_id = int(c_tok.value)
                else:
                    prop = self._current().value
                    self.pos += 1
                    self._expect(TokenType.EQUALS, "Ожидался '='.")
                    v_expr = self._parse_expression()
                    extra_opts[prop] = v_expr
                self._match(TokenType.COMMA)
            self._expect(TokenType.RBRACE, "Ожидался '}'.")
            span = SourceSpan(send_tok.span.line, send_tok.span.column, 9, self.file_path)
            return SendPollStmt(question=question_expr, options=options_list, is_quiz=is_quiz, correct_id=correct_id, extra=extra_opts, span=span)

        # Проверка на чек-лист: send checklist "..." { task "A" }
        if next_tok.type == TokenType.CHECKLIST:
            self.pos += 1
            title_expr = self._parse_expression()
            self._expect(TokenType.LBRACE, "Ожидался '{' для задач чек-листа.")
            tasks = []
            while self._current().type != TokenType.RBRACE and self._current().type != TokenType.EOF:
                self._expect(TokenType.TASK, "Ожидалось ключевое слово 'task'.")
                t_str = self._expect(TokenType.STRING, "Текст задачи должен быть в кавычках.")
                tasks.append(t_str.value)
            self._expect(TokenType.RBRACE, "Ожидался '}'.")
            span = SourceSpan(send_tok.span.line, send_tok.span.column, 14, self.file_path)
            return SendChecklistStmt(title=title_expr, tasks=tasks, span=span)

        # Проверка на rich: send rich { heading "..."; paragraph "..."; table { ... } }
        if next_tok.type == TokenType.RICH:
            self.pos += 1
            self._expect(TokenType.LBRACE, "Ожидался '{' для блоков rich message.")
            blocks = []
            while self._current().type != TokenType.RBRACE and self._current().type != TokenType.EOF:
                block_type_tok = self._expect(TokenType.IDENTIFIER, "Ожидался тип блока (heading, paragraph, quote, table, photo).")
                b_type = block_type_tok.value
                if b_type == "table":
                    self._expect(TokenType.LBRACE, "Ожидался '{' для таблицы.")
                    rows = []
                    while self._current().type != TokenType.RBRACE and self._current().type != TokenType.EOF:
                        self._expect(TokenType.IDENTIFIER, "Ожидалось 'row'.")
                        row_items = []
                        r_first = self._expect(TokenType.STRING, "Элемент таблицы должен быть строкой.")
                        row_items.append(r_first.value)
                        while self._match(TokenType.COMMA):
                            r_next = self._expect(TokenType.STRING, "Элемент таблицы должен быть строкой.")
                            row_items.append(r_next.value)
                        rows.append(row_items)
                    self._expect(TokenType.RBRACE, "Ожидался '}' для закрытия таблицы.")
                    blocks.append({"type": "table", "rows": rows})
                else:
                    text_tok = self._expect(TokenType.STRING, f"Текст для блока '{b_type}' должен быть в кавычках.")
                    blocks.append({"type": b_type, "text": text_tok.value})
            self._expect(TokenType.RBRACE, "Ожидался '}' для закрытия rich.")
            span = SourceSpan(send_tok.span.line, send_tok.span.column, 9, self.file_path)
            return SendRichStmt(blocks=blocks, span=span)

        # Проверка на отправку медиа: send photo "path.png" { caption = "..." }
        if next_tok.type in MEDIA_TOKENS:
            media_type = MEDIA_TOKENS[next_tok.type]
            self.pos += 1
            file_expr = self._parse_expression()
            options: dict[str, Any] = {}
            if self._current().type == TokenType.LBRACE:
                options = self._parse_config_block()
            span = SourceSpan(send_tok.span.line, send_tok.span.column, len(media_type) + 5, self.file_path)
            return SendMediaStmt(media_type=media_type, file_path=file_expr, options=options, span=span)

        msg_expr = self._parse_expression()
        span = SourceSpan(send_tok.span.line, send_tok.span.column, 4, self.file_path)
        return SendStmt(message=msg_expr, span=span)

    def _parse_ask_stmt(self) -> AskStmt:
        ask_tok = self._expect(TokenType.ASK, "Ожидалась инструкция 'ask'.")
        prompt = self._parse_expression()
        span = SourceSpan(ask_tok.span.line, ask_tok.span.column, 3, self.file_path)
        return AskStmt(prompt=prompt, span=span)

    def _parse_set_state_stmt(self) -> SetStateStmt:
        state_tok = self._expect(TokenType.STATE, "Ожидалась инструкция 'state'.")
        name_tok = self._expect(TokenType.IDENTIFIER, "Ожидалось имя состояния FSM.", hint="Пример: state register_name")
        span = SourceSpan(state_tok.span.line, state_tok.span.column, len(name_tok.value) + 6, self.file_path)
        return SetStateStmt(state_name=name_tok.value, span=span)

    def _parse_save_stmt(self) -> SaveStmt:
        save_tok = self._expect(TokenType.SAVE, "Ожидалась инструкция 'save'.")
        target = self._parse_expression()
        self._expect(TokenType.EQUALS, "Ожидался '=' после целевой переменной.")
        val_expr = self._parse_expression()
        span = SourceSpan(save_tok.span.line, save_tok.span.column, 4, self.file_path)
        return SaveStmt(target=target, value=val_expr, span=span)

    def _parse_log_stmt(self) -> LogStmt:
        log_tok = self._current()
        self.pos += 1
        is_error = log_tok.type == TokenType.LOG_ERROR
        msg_expr = self._parse_expression()
        span = SourceSpan(log_tok.span.line, log_tok.span.column, len(log_tok.value), self.file_path)
        return LogStmt(message=msg_expr, is_error=is_error, span=span)

    def _parse_stream_ai_stmt(self) -> StreamAiStmt:
        stream_tok = self._expect(TokenType.STREAM, "Ожидалось ключевое слово 'stream'.")
        var_tok = self._expect(TokenType.IDENTIFIER, "Ожидалось имя переменной для стрима.")
        self._expect(TokenType.FROM, "Ожидалось ключевое слово 'from'.")
        self._expect(TokenType.AI, "Ожидалось ключевое слово 'ai'.")
        ai_name_tok = self._expect(TokenType.IDENTIFIER, "Ожидалось имя ИИ-провайдера.")
        prompt_expr = self._parse_expression()
        span = SourceSpan(stream_tok.span.line, stream_tok.span.column, 6, self.file_path)
        return StreamAiStmt(var_name=var_tok.value, ai_name=ai_name_tok.value, prompt=prompt_expr, span=span)

    def _parse_broadcast_stmt(self) -> BroadcastStmt:
        b_tok = self._expect(TokenType.BROADCAST, "Ожидалось ключевое слово 'broadcast'.")
        msg_expr = self._parse_expression()
        span = SourceSpan(b_tok.span.line, b_tok.span.column, 9, self.file_path)
        return BroadcastStmt(message=msg_expr, span=span)

    def _parse_send_to_stmt(self) -> SendToStmt:
        st_tok = self._expect(TokenType.SEND_TO, "Ожидалось ключевое слово 'send_to'.")
        target_expr = self._parse_expression()
        msg_expr = self._parse_expression()
        span = SourceSpan(st_tok.span.line, st_tok.span.column, 7, self.file_path)
        return SendToStmt(target=target_expr, message=msg_expr, span=span)

    def _parse_send_invoice_stmt(self) -> SendInvoiceStmt:
        inv_tok = self._expect(TokenType.SEND_INVOICE, "Ожидалось ключевое слово 'send_invoice'.")
        self._expect(TokenType.LBRACE, "Ожидался '{' для параметров инвойса.")
        opts = {}
        while self._current().type != TokenType.RBRACE and self._current().type != TokenType.EOF:
            prop = self._current().value
            self.pos += 1
            self._expect(TokenType.EQUALS, "Ожидался '='.")
            # Цена может быть "100 stars" или число
            if prop == "price":
                val_tok = self._current()
                self.pos += 1
                opts["price"] = val_tok.value
                if self._current().type == TokenType.IDENTIFIER:
                    opts["currency"] = self._current().value
                    self.pos += 1
            else:
                val_expr = self._parse_expression()
                opts[prop] = val_expr.value if hasattr(val_expr, "value") else str(val_expr)
            self._match(TokenType.COMMA)
        self._expect(TokenType.RBRACE, "Ожидался '}'.")
        span = SourceSpan(inv_tok.span.line, inv_tok.span.column, 12, self.file_path)
        return SendInvoiceStmt(options=opts, span=span)

    def _parse_react_stmt(self) -> ReactStmt:
        react_tok = self._expect(TokenType.REACT, "Ожидалось ключевое слово 'react'.")
        target_expr = self._parse_expression()
        self._expect(TokenType.WITH, "Ожидалось ключевое слово 'with'.")
        emoji_expr = self._parse_expression()
        span = SourceSpan(react_tok.span.line, react_tok.span.column, 5, self.file_path)
        return ReactStmt(target=target_expr, emoji=emoji_expr, span=span)

    def _parse_remove_reaction_stmt(self) -> RemoveReactionStmt:
        rr_tok = self._expect(TokenType.REMOVE_REACTION, "Ожидалось ключевое слово 'remove_reaction'.")
        target_expr = self._parse_expression()
        span = SourceSpan(rr_tok.span.line, rr_tok.span.column, 15, self.file_path)
        return RemoveReactionStmt(target=target_expr, span=span)

    def _parse_if_stmt(self) -> IfStmt:
        if_tok = self._expect(TokenType.IF, "Ожидалось ключевое слово 'if'.")
        condition = self._parse_expression()
        then_branch = self._parse_block()

        else_branch: Optional[Block] = None
        if self._match(TokenType.ELSE):
            if self._current().type == TokenType.IF:
                nested_if = self._parse_if_stmt()
                else_branch = Block(statements=[nested_if], span=nested_if.span)
            else:
                else_branch = self._parse_block()

        span = SourceSpan(if_tok.span.line, if_tok.span.column, 2, self.file_path)
        return IfStmt(condition=condition, then_branch=then_branch, else_branch=else_branch, span=span)

    def _parse_buttons_block(self) -> ButtonsBlock:
        btn_tok = self._expect(TokenType.BUTTONS, "Ожидалось ключевое слово 'buttons'.")
        self._expect(TokenType.LBRACE, "Ожидался символ '{' для начала блока buttons.")
        buttons: list[ButtonDef] = []

        while self._current().type != TokenType.RBRACE and self._current().type != TokenType.EOF:
            label_tok = self._expect(TokenType.STRING, "Текст кнопки должен быть строкой в кавычках.")
            self._expect(TokenType.ARROW, f"Ожидалась стрелка '->' после текста кнопки {label_tok.value!r}.")
            target = self._parse_expression()

            # Дополнительные свойства: { style = "primary", icon_emoji = "🔥" }
            style = None
            icon_emoji = None
            if self._current().type == TokenType.LBRACE:
                opts = self._parse_config_block()
                style = opts.get("style")
                icon_emoji = opts.get("icon_emoji")

            btn_span = SourceSpan(label_tok.span.line, label_tok.span.column, len(label_tok.value), self.file_path)
            buttons.append(ButtonDef(label=label_tok.value, target=target, style=style, icon_emoji=icon_emoji, span=btn_span))

        self._expect(TokenType.RBRACE, "Ожидался символ '}' для закрытия блока buttons.")
        span = SourceSpan(btn_tok.span.line, btn_tok.span.column, 7, self.file_path)
        return ButtonsBlock(buttons=buttons, span=span)

    # ==========================================
    # ВЫРАЖЕНИЯ (Expressions)
    # ==========================================

    def _parse_expression(self) -> Expr:
        # Проверка на вызов API: call weather with { q: "Moscow" }
        if self._current().type == TokenType.CALL:
            return self._parse_call_api_expr()

        return self._parse_comparison()

    def _parse_call_api_expr(self) -> CallApiExpr:
        call_tok = self._expect(TokenType.CALL, "Ожидалось ключевое слово 'call'.")
        api_name_tok = self._expect(TokenType.IDENTIFIER, "Ожидалось имя API.", hint="Пример: call weather with { ... }")
        self._expect(TokenType.WITH, "Ожидалось ключевое слово 'with'.")
        self._expect(TokenType.LBRACE, "Ожидался символ '{' для параметров API запроса.")

        params: dict[str, Expr] = {}
        while self._current().type != TokenType.RBRACE and self._current().type != TokenType.EOF:
            p_name_tok = self._expect(TokenType.IDENTIFIER, "Ожидалось имя параметра запроса.")
            self._expect(TokenType.COLON if self._current().type == TokenType.COLON else TokenType.EQUALS, "Ожидался ':' или '='.")
            p_val_expr = self._parse_expression()
            params[p_name_tok.value] = p_val_expr
            self._match(TokenType.COMMA)

        self._expect(TokenType.RBRACE, "Ожидался символ '}' для закрытия параметров API.")
        span = SourceSpan(call_tok.span.line, call_tok.span.column, len(api_name_tok.value) + 5, self.file_path)
        return CallApiExpr(api_name=api_name_tok.value, params=params, span=span)

    def _parse_comparison(self) -> Expr:
        left = self._parse_additive()

        while self._current().type in (
            TokenType.EQEQ,
            TokenType.NOT_EQ,
            TokenType.LT,
            TokenType.GT,
            TokenType.LTE,
            TokenType.GTE,
            TokenType.CONTAINS,
        ):
            op_tok = self._current()
            self.pos += 1
            right = self._parse_additive()
            span = SourceSpan(left.span.line, left.span.column, max(1, right.span.column - left.span.column), self.file_path)
            left = BinaryExpr(left=left, op=op_tok.value, right=right, span=span)

        return left

    def _parse_additive(self) -> Expr:
        left = self._parse_multiplicative()

        while self._current().type in (TokenType.PLUS, TokenType.MINUS):
            op_tok = self._current()
            self.pos += 1
            right = self._parse_multiplicative()
            span = SourceSpan(left.span.line, left.span.column, max(1, right.span.column - left.span.column), self.file_path)
            left = BinaryExpr(left=left, op=op_tok.value, right=right, span=span)

        return left

    def _parse_multiplicative(self) -> Expr:
        left = self._parse_postfix()

        while self._current().type in (TokenType.STAR, TokenType.SLASH):
            op_tok = self._current()
            self.pos += 1
            right = self._parse_postfix()
            span = SourceSpan(left.span.line, left.span.column, max(1, right.span.column - left.span.column), self.file_path)
            left = BinaryExpr(left=left, op=op_tok.value, right=right, span=span)

        return left

    def _parse_postfix(self) -> Expr:
        expr = self._parse_primary()

        while True:
            # Доступ к полям: expr.member (user.coins, message.text)
            if self._match(TokenType.DOT):
                member_tok = self._expect(TokenType.IDENTIFIER, "Ожидалось имя свойства после точки.")
                span = SourceSpan(expr.span.line, expr.span.column, len(member_tok.value) + 1, self.file_path)
                expr = MemberAccessExpr(target=expr, member=member_tok.value, span=span)
                continue

            # Вызов функции: expr(args...)
            if self._match(TokenType.LPAREN):
                args: list[Expr] = []
                if self._current().type != TokenType.RPAREN:
                    args.append(self._parse_expression())
                    while self._match(TokenType.COMMA):
                        args.append(self._parse_expression())
                self._expect(TokenType.RPAREN, "Ожидалась закрывающая скобка ')' после аргументов.")
                func_name = expr.name if isinstance(expr, Identifier) else str(expr)
                span = SourceSpan(expr.span.line, expr.span.column, 1, self.file_path)
                expr = FunctionCallExpr(func_name=func_name, args=args, span=span)
                continue

            break

        return expr

    def _parse_primary(self) -> Expr:
        tok = self._current()

        if tok.type == TokenType.STRING:
            self.pos += 1
            return StringLiteral(value=tok.value, span=tok.span)

        if tok.type == TokenType.NUMBER:
            self.pos += 1
            return NumberLiteral(value=tok.value, span=tok.span)

        if tok.type == TokenType.TRUE:
            self.pos += 1
            return BooleanLiteral(value=True, span=tok.span)

        if tok.type == TokenType.FALSE:
            self.pos += 1
            return BooleanLiteral(value=False, span=tok.span)

        if tok.type in (TokenType.IDENTIFIER, TokenType.RESULT):
            self.pos += 1
            return Identifier(name=tok.value, span=tok.span)

        if tok.type == TokenType.MESSAGE:
            self.pos += 1
            return Identifier(name="message", span=tok.span)

        if tok.type == TokenType.URL:
            self.pos += 1
            return Identifier(name="url", span=tok.span)

        if self._match(TokenType.LBRACKET):
            items = []
            if self._current().type != TokenType.RBRACKET:
                items.append(self._parse_expression())
                while self._match(TokenType.COMMA):
                    items.append(self._parse_expression())
            self._expect(TokenType.RBRACKET, "Ожидалась закрывающая скобка ']' для списка.")
            return ListLiteral(items=items, span=tok.span)

        if self._match(TokenType.LPAREN):
            inner = self._parse_expression()
            self._expect(TokenType.RPAREN, "Ожидалась закрывающая скобка ')'.")
            return inner

        raise TeleLangSyntaxError(
            f"Ожидалось выражение, но получено '{tok.value}'.",
            span=tok.span,
            source_code=self.source,
            hint='Например: строка "...", число 100 или переменная.',
        )
