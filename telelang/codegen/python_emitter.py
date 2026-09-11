"""Генератор Python-кода (Code Emitter) на базе aiogram 3.x (Этап 3)."""

from __future__ import annotations
import re
import time
from typing import Any, Optional
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
    Expr,
    ExprStmt,
    FunctionCallExpr,
    FunctionDecl,
    HookDecl,
    Identifier,
    IfStmt,
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


class PythonEmitter:
    """Транслирует AST-дерево TeleLang в исполняемый Python-код на aiogram 3."""

    def __init__(self, program: Program):
        self.program = program
        self.bot_name: str = "TeleBot"
        self.mode: str = "polling"
        self.webhook_url: str = ""
        self.webhook_port: int = 8443
        self.commands: list[CommandDecl] = []
        self.on_messages: list[OnMessageDecl] = []
        self.functions: list[FunctionDecl] = []
        self.states: list[StateDecl] = []
        self.databases: list[DatabaseDecl] = []
        self.apis: list[ApiDecl] = []
        self.hooks: list[HookDecl] = []
        self.roles_decl: Optional[RolesDecl] = None
        self.callbacks: list[tuple[str, str, FunctionCallExpr]] = []
        self.callback_counter: int = 0
        # Этап 4
        self.ais: list[AiDecl] = []
        self.schedulers: list[SchedulerDecl] = []
        self.antispam: Optional[AntispamDecl] = None
        self.locales: Optional[LocalesDecl] = None
        self.inlines: list[InlineQueryDecl] = []
        self.analytics: Optional[AnalyticsDecl] = None

    def emit(self) -> str:
        """Генерирует полный исходный код Python-файла."""
        for decl in self.program.declarations:
            if isinstance(decl, BotDecl):
                self.bot_name = decl.name
                self.mode = decl.config.get("mode", "polling")
                self.webhook_url = decl.config.get("webhook_url", "")
                self.webhook_port = int(decl.config.get("webhook_port", 8443))
            elif isinstance(decl, CommandDecl):
                self.commands.append(decl)
            elif isinstance(decl, OnMessageDecl):
                self.on_messages.append(decl)
            elif isinstance(decl, FunctionDecl):
                self.functions.append(decl)
            elif isinstance(decl, StateDecl):
                self.states.append(decl)
            elif isinstance(decl, DatabaseDecl):
                self.databases.append(decl)
            elif isinstance(decl, ApiDecl):
                self.apis.append(decl)
            elif isinstance(decl, HookDecl):
                self.hooks.append(decl)
            elif isinstance(decl, RolesDecl):
                self.roles_decl = decl
            elif isinstance(decl, AiDecl):
                self.ais.append(decl)
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

        lines: list[str] = [
            "# -*- coding: utf-8 -*-",
            "# Сгенерировано компилятором TeleLang. Не редактируйте вручную.",
            "import asyncio",
            "import logging",
            "import os",
            "import sys",
            "import time",
            "from pathlib import Path",
            "import aiohttp",
            "import aiosqlite",
            "from aiogram import Bot, Dispatcher, Router, types, F",
            "from aiogram.filters import Command, ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER",
            "from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile",
            "from aiogram.fsm.state import State, StatesGroup",
            "from aiogram.fsm.context import FSMContext",
            "",
            "logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')",
            f"logger = logging.getLogger({self.bot_name!r})",
            "",
            "router = Router()",
            "",
            "# Утилиты данных и DotDict для API",
            "class _DotDict(dict):",
            "    def __getattr__(self, name):",
            "        val = self.get(name)",
            "        if isinstance(val, dict):",
            "            return _DotDict(val)",
            "        return val",
            "    def __setattr__(self, name, value):",
            "        self[name] = value",
            "",
            "# Вспомогательные классы контекста TeleLang",
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

        # 1. Генерация FSM состояний
        if self.states:
            lines.append("class _TeleStates(StatesGroup):")
            for st in self.states:
                lines.append(f"    {st.name} = State()")
            lines.append("")

        # 2. База данных SQLite
        lines.extend(self._emit_database_layer())

        # 2.1. Локализация (i18n)
        if self.locales:
            lines.extend(self._emit_locales_layer(self.locales))
            lines.append("")

        # 3. Внешние API функции
        for api in self.apis:
            lines.extend(self._emit_api_client(api))
            lines.append("")

        # 3.1. ИИ клиенты (ai openai { ... })
        for ai in self.ais:
            lines.extend(self._emit_ai_client(ai))
            lines.append("")

        # 3.2. Антиспам middleware
        if self.antispam and self.antispam.enabled:
            lines.extend(self._emit_antispam_middleware(self.antispam))
            lines.append("")

        # 4. Пользовательские функции
        for fn in self.functions:
            lines.extend(self._emit_user_function(fn))
            lines.append("")

        # 5. Хуки before_command / after_command
        before_hooks = [h for h in self.hooks if h.hook_type == "before_command"]
        after_hooks = [h for h in self.hooks if h.hook_type == "after_command"]
        error_hooks = [h for h in self.hooks if h.hook_type == "on_error"]

        if before_hooks or after_hooks:
            lines.extend(self._emit_middleware(before_hooks, after_hooks))

        if error_hooks:
            lines.extend(self._emit_error_handler(error_hooks[0]))

        # 6. Команды бота
        for idx, cmd in enumerate(self.commands):
            lines.extend(self._emit_command(cmd, idx))
            lines.append("")

        # 7. Обработчики состояний FSM
        for st in self.states:
            lines.extend(self._emit_state_handler(st))
            lines.append("")

        # 8. on message
        for idx, on_msg in enumerate(self.on_messages):
            lines.extend(self._emit_on_message(on_msg, idx))
            lines.append("")

        # 9. Хуки участников чата (join / leave)
        join_hooks = [h for h in self.hooks if h.hook_type == "on_member_join"]
        leave_hooks = [h for h in self.hooks if h.hook_type == "on_member_leave"]

        for idx, h in enumerate(join_hooks):
            lines.extend(self._emit_chat_member_hook(h, is_join=True, index=idx))
            lines.append("")

        for idx, h in enumerate(leave_hooks):
            lines.extend(self._emit_chat_member_hook(h, is_join=False, index=idx))
            lines.append("")

        # 9.1. Специальные хуки (on_payment, on_join_request, on_poll_answer, on_checklist_task_done)
        special_hooks = [h for h in self.hooks if h.hook_type in ("on_payment", "on_join_request", "on_poll_answer", "on_checklist_task_done")]
        for idx, h in enumerate(special_hooks):
            lines.extend(self._emit_special_hook(h, idx))
            lines.append("")

        # 9.2. Inline Query
        for idx, iq in enumerate(self.inlines):
            lines.extend(self._emit_inline_query(iq, idx))
            lines.append("")

        # 10. Callback-обработчики кнопок
        for cb_id, _, call_expr in self.callbacks:
            lines.extend(self._emit_callback_handler(cb_id, call_expr))
            lines.append("")

        # 10.1. Фоновые задачи планировщика
        if self.schedulers:
            lines.extend(self._emit_scheduler_tasks())
            lines.append("")

        # 11. Фабрика и запуск бота (polling или webhook)
        lines.extend(self._emit_runner_functions())

        return "\n".join(lines)

    def _emit_database_layer(self) -> list[str]:
        lines = [
            "DB_PATH = Path('database/bot.db')",
            "async def _init_database():",
            "    DB_PATH.parent.mkdir(parents=True, exist_ok=True)",
            "    async with aiosqlite.connect(DB_PATH) as db:",
        ]

        if self.databases:
            for db_decl in self.databases:
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
            "        await db.execute('INSERT INTO users (user_id) VALUES (?) ON CONFLICT(user_id) DO NOTHING', (user_id,))",
            "        await db.execute(f'UPDATE users SET {field} = ? WHERE user_id = ?', (value, user_id))",
            "        await db.commit()",
            "",
            "async def _update_user_db(user_id: int, field: str, delta):",
            "    async with aiosqlite.connect(DB_PATH) as db:",
            "        await db.execute('INSERT INTO users (user_id) VALUES (?) ON CONFLICT(user_id) DO NOTHING', (user_id,))",
            "        await db.execute(f'UPDATE users SET {field} = COALESCE({field}, 0) + ? WHERE user_id = ?', (delta, user_id))",
            "        await db.commit()",
            "",
        ])
        return lines

    def _emit_api_client(self, api: ApiDecl) -> list[str]:
        headers_repr = repr(api.headers)
        lines = [
            f"async def _call_api_{api.name}(params: dict) -> _DotDict:",
            "    async with aiohttp.ClientSession() as session:",
            f"        url = {api.url!r}",
            f"        headers = {headers_repr}",
            "        async with session.get(url, params=params, headers=headers) as resp:",
            "            try:",
            "                data = await resp.json()",
            "                return _DotDict(data)",
            "            except Exception:",
            "                text = await resp.text()",
            "                return _DotDict({'text': text})",
        ]
        return lines

    def _emit_middleware(self, before_hooks: list[HookDecl], after_hooks: list[HookDecl]) -> list[str]:
        lines = [
            "from aiogram import BaseMiddleware",
            "class _HookMiddleware(BaseMiddleware):",
            "    async def __call__(self, handler, event, data):",
            "        _msg_target = event if isinstance(event, types.Message) else getattr(event, 'message', None)",
            "        user = _CtxUser(event.from_user)",
            "        chat = _CtxChat(_msg_target.chat if _msg_target else None)",
            "        _start_time = time.perf_counter()",
        ]
        if before_hooks:
            lines.extend(self._emit_block(before_hooks[0].body, indent=8))

        lines.extend([
            "        result = await handler(event, data)",
            "        elapsed_ms = int((time.perf_counter() - _start_time) * 1000)",
        ])

        if after_hooks:
            lines.extend(self._emit_block(after_hooks[0].body, indent=8))

        lines.extend([
            "        return result",
            "",
            "router.message.middleware(_HookMiddleware())",
            "",
        ])
        return lines

    def _emit_error_handler(self, hook: HookDecl) -> list[str]:
        lines = [
            "@router.error()",
            "async def _handle_global_error(event: types.ErrorEvent):",
            "    error = event.exception",
            "    _msg_target = event.update.message if event.update else None",
            "    user = _CtxUser(_msg_target.from_user if _msg_target else None)",
        ]
        body = self._emit_block(hook.body, indent=4)
        lines.extend(body if body else ["    logger.exception(error)"])
        lines.append("")
        return lines

    def _emit_user_function(self, fn: FunctionDecl) -> list[str]:
        param_list = ["_msg_target=None", "_user=None"] + fn.params
        params_str = ", ".join(param_list)

        lines = [
            f"async def {fn.name}({params_str}):",
            "    user = _user if _user is not None else (_CtxUser(_msg_target.from_user) if _msg_target else _CtxUser(None))",
            "    if user.id > 0:",
            "        user.coins = await _get_user_db(user.id, 'coins', 0)",
            "    message = _CtxMsg(_msg_target) if _msg_target else _CtxMsg(None)",
            "    chat = _CtxChat(_msg_target.chat) if _msg_target else _CtxChat(None)",
        ]

        body_lines = self._emit_block(fn.body, indent=4)
        if not body_lines:
            body_lines = ["    pass"]
        lines.extend(body_lines)
        return lines

    def _emit_command(self, cmd: CommandDecl, index: int) -> list[str]:
        clean_command = cmd.command.lstrip("/")
        func_name = f"_handle_cmd_{clean_command}_{index}"

        lines = [
            f"@router.message(Command({clean_command!r}))",
            f"async def {func_name}(message: types.Message, state: FSMContext = None):",
            "    _msg_target = message",
            "    user = _CtxUser(message.from_user)",
            "    user.coins = await _get_user_db(user.id, 'coins', 0)",
            "    chat = _CtxChat(message.chat)",
        ]

        # Проверка прав (only admin / only role)
        if cmd.permission == "admin":
            lines.extend([
                "    admin_id = int(os.environ.get('BOT_ADMIN_ID', '0'))",
                "    if message.from_user.id != admin_id:",
                "        await message.answer('У вас нет прав администратора.')",
                "        return",
            ])
        elif cmd.permission and "role:" in cmd.permission:
            role_name = cmd.permission.split("role:")[1].split()[0]
            lines.extend([
                f"    async with aiosqlite.connect(DB_PATH) as _db:",
                f"        async with _db.execute('SELECT 1 FROM user_roles WHERE user_id = ? AND role = ?', (user.id, {role_name!r})) as _cur:",
                "            if not (await _cur.fetchone()):",
                "                await message.answer('Доступ запрещён: требуется роль.')",
                "                return",
            ])

        body_lines = self._emit_block(cmd.body, indent=4)
        if not body_lines:
            body_lines = ["    pass"]
        lines.extend(body_lines)
        return lines

    def _emit_state_handler(self, st: StateDecl) -> list[str]:
        func_name = f"_handle_state_{st.name}"
        lines = [
            f"@router.message(_TeleStates.{st.name})",
            f"async def {func_name}(message: types.Message, state: FSMContext):",
            "    _msg_target = message",
            "    user = _CtxUser(message.from_user)",
            "    user.coins = await _get_user_db(user.id, 'coins', 0)",
            "    chat = _CtxChat(message.chat)",
        ]

        body_lines = self._emit_block(st.body, indent=4)
        if not body_lines:
            body_lines = ["    pass"]
        lines.extend(body_lines)
        # Очищаем состояние в конце обработчика
        lines.append("    await state.clear()")
        return lines

    def _emit_on_message(self, on_msg: OnMessageDecl, index: int) -> list[str]:
        func_name = f"_handle_on_message_{index}"

        lines = [
            "@router.message()",
            f"async def {func_name}(message: types.Message, state: FSMContext = None):",
            "    _msg_target = message",
            "    user = _CtxUser(message.from_user)",
            "    user.coins = await _get_user_db(user.id, 'coins', 0)",
            "    chat = _CtxChat(message.chat)",
        ]

        body_lines = self._emit_block(on_msg.body, indent=4)
        if not body_lines:
            body_lines = ["    pass"]
        lines.extend(body_lines)
        return lines

    def _emit_chat_member_hook(self, hook: HookDecl, is_join: bool, index: int) -> list[str]:
        trans = "IS_MEMBER" if is_join else "IS_NOT_MEMBER"
        func_name = f"_handle_member_{'join' if is_join else 'leave'}_{index}"

        lines = [
            f"@router.chat_member(ChatMemberUpdatedFilter({trans}))",
            f"async def {func_name}(event: types.ChatMemberUpdated):",
            "    user = _CtxUser(event.new_chat_member.user if event.new_chat_member else event.from_user)",
            "    chat = _CtxChat(event.chat)",
            "    _msg_target = event",
        ]
        body = self._emit_block(hook.body, indent=4)
        lines.extend(body if body else ["    pass"])
        return lines

    def _emit_callback_handler(self, cb_id: str, call_expr: FunctionCallExpr) -> list[str]:
        func_name = f"_cb_{cb_id}"
        lines = [
            f"@router.callback_query(F.data == {cb_id!r})",
            f"async def {func_name}(callback: types.CallbackQuery, state: FSMContext = None):",
            "    await callback.answer()",
            "    _msg_target = callback.message",
            "    user = _CtxUser(callback.from_user)",
            "    user.coins = await _get_user_db(user.id, 'coins', 0)",
            "    chat = _CtxChat(callback.message.chat if callback.message else None)",
        ]

        args_str = ", ".join([self._emit_expression(a) for a in call_expr.args])
        call_args = "_msg_target, _user=user" + (f", {args_str}" if args_str else "")
        call_line = f"    await {call_expr.func_name}({call_args})"
        lines.append(call_line)
        return lines

    def _emit_block(self, block: Block, indent: int = 4) -> list[str]:
        lines: list[str] = []
        pad = " " * indent

        buttons_block: Optional[ButtonsBlock] = None
        for stmt in block.statements:
            if isinstance(stmt, ButtonsBlock):
                buttons_block = stmt
                break

        for stmt in block.statements:
            if isinstance(stmt, ButtonsBlock):
                continue

            if isinstance(stmt, SendStmt):
                if buttons_block:
                    kb_lines = self._emit_keyboard_builder(buttons_block, indent=indent)
                    lines.extend(kb_lines)
                    msg_code = self._emit_expression(stmt.message)
                    lines.append(f"{pad}await _msg_target.answer({msg_code}, reply_markup=_keyboard)")
                    buttons_block = None
                else:
                    msg_code = self._emit_expression(stmt.message)
                    lines.append(f"{pad}await _msg_target.answer({msg_code})")

            elif isinstance(stmt, SendMediaStmt):
                lines.extend(self._emit_send_media(stmt, indent, buttons_block))
                buttons_block = None

            elif isinstance(stmt, AskStmt):
                prompt_code = self._emit_expression(stmt.prompt)
                lines.append(f"{pad}await _msg_target.answer({prompt_code})")

            elif isinstance(stmt, SetStateStmt):
                lines.append(f"{pad}if state is not None:")
                lines.append(f"{pad}    await state.set_state(_TeleStates.{stmt.state_name})")

            elif isinstance(stmt, SaveStmt):
                # save user.name = message.text
                if isinstance(stmt.target, MemberAccessExpr) and isinstance(stmt.target.target, Identifier):
                    field_name = stmt.target.member
                    val_code = self._emit_expression(stmt.value)
                    lines.append(f"{pad}await _set_user_db(user.id, {field_name!r}, {val_code})")
                else:
                    target_code = self._emit_expression(stmt.target)
                    val_code = self._emit_expression(stmt.value)
                    lines.append(f"{pad}{target_code} = {val_code}")

            elif isinstance(stmt, AugAssignStmt):
                # user.coins += 10
                if isinstance(stmt.target, MemberAccessExpr) and isinstance(stmt.target.target, Identifier):
                    field_name = stmt.target.member
                    val_code = self._emit_expression(stmt.value)
                    delta_sign = "" if stmt.op == "+=" else "-"
                    lines.append(f"{pad}await _update_user_db(user.id, {field_name!r}, {delta_sign}{val_code})")
                else:
                    target_code = self._emit_expression(stmt.target)
                    val_code = self._emit_expression(stmt.value)
                    lines.append(f"{pad}{target_code} {stmt.op} {val_code}")

            elif isinstance(stmt, LogStmt):
                msg_code = self._emit_expression(stmt.message)
                log_fn = "logger.error" if stmt.is_error else "logger.info"
                lines.append(f"{pad}{log_fn}({msg_code})")

            elif isinstance(stmt, VariableAssignStmt):
                val_code = self._emit_expression(stmt.value)
                lines.append(f"{pad}{stmt.name} = {val_code}")

            elif isinstance(stmt, IfStmt):
                cond_code = self._emit_expression(stmt.condition)
                lines.append(f"{pad}if {cond_code}:")
                then_lines = self._emit_block(stmt.then_branch, indent=indent + 4)
                lines.extend(then_lines if then_lines else [f"{pad}    pass"])

                if stmt.else_branch:
                    lines.append(f"{pad}else:")
                    else_lines = self._emit_block(stmt.else_branch, indent=indent + 4)
                    lines.extend(else_lines if else_lines else [f"{pad}    pass"])

            elif isinstance(stmt, ExprStmt):
                expr_code = self._emit_expression(stmt.expr)
                lines.append(f"{pad}{expr_code}")

            elif isinstance(stmt, StreamAiStmt):
                prompt_code = self._emit_expression(stmt.prompt)
                lines.extend([
                    f"{pad}# Стриминг ИИ",
                    f"{pad}_stream_msg = await _msg_target.answer('⏳ Генерация ответа...')",
                    f"{pad}async def _do_stream():",
                    f"{pad}    _accum = ''",
                    f"{pad}    async for _chunk in _stream_ai_{stmt.ai_name}({prompt_code}):",
                    f"{pad}        _accum += _chunk",
                    f"{pad}        if len(_accum) % 20 == 0:",
                    f"{pad}            try: await _stream_msg.edit_text(_accum)",
                    f"{pad}            except Exception: pass",
                    f"{pad}    try: await _stream_msg.edit_text(_accum or 'Пустой ответ.')",
                    f"{pad}    except Exception: pass",
                    f"{pad}await _do_stream()",
                ])

            elif isinstance(stmt, BroadcastStmt):
                msg_code = self._emit_expression(stmt.message)
                lines.extend([
                    f"{pad}async with aiosqlite.connect(DB_PATH) as _db:",
                    f"{pad}    async with _db.execute('SELECT user_id FROM users') as _cur:",
                    f"{pad}        async for _row in _cur:",
                    f"{pad}            try: await _msg_target.bot.send_message(_row[0], {msg_code})",
                    f"{pad}            except Exception: pass",
                ])

            elif isinstance(stmt, SendToStmt):
                msg_code = self._emit_expression(stmt.message)
                if isinstance(stmt.target, Identifier) and stmt.target.name == "admin":
                    lines.append(f"{pad}await _msg_target.bot.send_message(int(os.environ.get('BOT_ADMIN_ID', '0')), {msg_code})")
                else:
                    tgt_code = self._emit_expression(stmt.target)
                    lines.append(f"{pad}await _msg_target.bot.send_message({tgt_code}, {msg_code})")

            elif isinstance(stmt, SendInvoiceStmt):
                title = repr(stmt.options.get("title", "Оплата"))
                desc = repr(stmt.options.get("description", "Оплата счёта"))
                price = int(stmt.options.get("price", 100))
                currency = str(stmt.options.get("currency", "XTR"))
                prov_tok = repr(stmt.options.get("provider_token", ""))
                lines.extend([
                    f"{pad}await _msg_target.answer_invoice(",
                    f"{pad}    title={title},",
                    f"{pad}    description={desc},",
                    f"{pad}    payload='tele_payload_{int(time.time())}',",
                    f"{pad}    provider_token={prov_tok},",
                    f"{pad}    currency={currency!r},",
                    f"{pad}    prices=[types.LabeledPrice(label={title}, amount={price})]",
                    f"{pad})",
                ])

            elif isinstance(stmt, ReactStmt):
                emoji_code = self._emit_expression(stmt.emoji)
                lines.append(f"{pad}try: await _msg_target.bot.set_message_reaction(_msg_target.chat.id, _msg_target.message_id, reaction=[types.ReactionTypeEmoji(emoji={emoji_code})])")
                lines.append(f"{pad}except Exception: pass")

            elif isinstance(stmt, RemoveReactionStmt):
                lines.append(f"{pad}try: await _msg_target.bot.set_message_reaction(_msg_target.chat.id, _msg_target.message_id, reaction=[])")
                lines.append(f"{pad}except Exception: pass")

            elif isinstance(stmt, SendPollStmt):
                q_code = self._emit_expression(stmt.question)
                opts_codes = "[" + ", ".join([self._emit_expression(o) for o in stmt.options]) + "]"
                if stmt.is_quiz:
                    lines.append(f"{pad}await _msg_target.answer_poll(question={q_code}, options={opts_codes}, type='quiz', correct_option_id={stmt.correct_id}, is_anonymous=False)")
                else:
                    lines.append(f"{pad}await _msg_target.answer_poll(question={q_code}, options={opts_codes}, is_anonymous=False)")

            elif isinstance(stmt, SendChecklistStmt):
                title_code = self._emit_expression(stmt.title)
                tasks_repr = repr(stmt.tasks)
                # Деградация чек-листа в красивое текстовое сообщение с чекбоксами [ ]
                lines.append(f"{pad}_tasks_text = '\\n'.join([f'⬜ {{t}}' for t in {tasks_repr}])")
                lines.append(f"{pad}await _msg_target.answer(f'📋 <b>{{{title_code}}}</b>\\n\\n{{_tasks_text}}', parse_mode='HTML')")

            elif isinstance(stmt, SendRichStmt):
                lines.append(f"{pad}_rich_parts = []")
                for blk in stmt.blocks:
                    b_type = blk.get("type")
                    if b_type == "heading":
                        lines.append(f"{pad}_rich_parts.append(f'<b>{blk.get('text', '')}</b>\\n')")
                    elif b_type == "paragraph":
                        lines.append(f"{pad}_rich_parts.append(f'{blk.get('text', '')}\\n')")
                    elif b_type == "quote":
                        lines.append(f"{pad}_rich_parts.append(f'<blockquote>{blk.get('text', '')}</blockquote>\\n')")
                    elif b_type == "table":
                        rows = blk.get("rows", [])
                        table_text = "\\n".join([" | ".join(r) for r in rows])
                        lines.append(f"{pad}_rich_parts.append(f'<pre>{table_text}</pre>\\n')")
                lines.append(f"{pad}await _msg_target.answer(''.join(_rich_parts), parse_mode='HTML')")

        if buttons_block:
            kb_lines = self._emit_keyboard_builder(buttons_block, indent=indent)
            lines.extend(kb_lines)
            lines.append(f"{pad}await _msg_target.answer('Выбери:', reply_markup=_keyboard)")

        return lines

    def _emit_send_media(self, stmt: SendMediaStmt, indent: int, buttons_block: Optional[ButtonsBlock]) -> list[str]:
        pad = " " * indent
        lines = []
        path_code = self._emit_expression(stmt.file_path)
        caption_code = repr(stmt.options.get("caption", ""))

        reply_markup = ""
        if buttons_block:
            kb_lines = self._emit_keyboard_builder(buttons_block, indent=indent)
            lines.extend(kb_lines)
            reply_markup = ", reply_markup=_keyboard"

        if stmt.media_type == "photo":
            lines.append(f"{pad}await _msg_target.answer_photo(FSInputFile({path_code}), caption={caption_code}{reply_markup})")
        elif stmt.media_type == "video_note":
            lines.append(f"{pad}await _msg_target.answer_video_note(FSInputFile({path_code}){reply_markup})")
        elif stmt.media_type == "document":
            lines.append(f"{pad}await _msg_target.answer_document(FSInputFile({path_code}), caption={caption_code}{reply_markup})")
        elif stmt.media_type == "video":
            lines.append(f"{pad}await _msg_target.answer_video(FSInputFile({path_code}), caption={caption_code}{reply_markup})")
        elif stmt.media_type == "audio":
            lines.append(f"{pad}await _msg_target.answer_audio(FSInputFile({path_code}), caption={caption_code}{reply_markup})")
        elif stmt.media_type == "voice":
            lines.append(f"{pad}await _msg_target.answer_voice(FSInputFile({path_code}){reply_markup})")
        elif stmt.media_type == "sticker":
            lines.append(f"{pad}await _msg_target.answer_sticker(FSInputFile({path_code}){reply_markup})")

        return lines

    def _emit_keyboard_builder(self, buttons_block: ButtonsBlock, indent: int) -> list[str]:
        pad = " " * indent
        lines = [f"{pad}_kb_builder = []"]

        for btn in buttons_block.buttons:
            # Деградация цвета/стиля и эмодзи: если icon_emoji указан, добавляем его к тексту кнопки
            label_text = btn.label
            if btn.icon_emoji and not label_text.startswith(btn.icon_emoji):
                label_text = f"{btn.icon_emoji} {label_text}"

            if isinstance(btn.target, FunctionCallExpr) and btn.target.func_name == "url":
                url_val = self._emit_expression(btn.target.args[0]) if btn.target.args else "''"
                lines.append(
                    f"{pad}_kb_builder.append([InlineKeyboardButton(text={label_text!r}, url={url_val})])"
                )
            elif isinstance(btn.target, FunctionCallExpr):
                self.callback_counter += 1
                cb_id = f"btn_{btn.target.func_name}_{self.callback_counter}"
                self.callbacks.append((cb_id, label_text, btn.target))
                lines.append(
                    f"{pad}_kb_builder.append([InlineKeyboardButton(text={label_text!r}, callback_data={cb_id!r})])"
                )
            else:
                lines.append(
                    f"{pad}_kb_builder.append([InlineKeyboardButton(text={label_text!r}, callback_data='cb_noop')])"
                )

        lines.append(f"{pad}_keyboard = InlineKeyboardMarkup(inline_keyboard=_kb_builder)")
        return lines

    def _emit_expression(self, expr: Expr) -> str:
        if isinstance(expr, StringLiteral):
            val = expr.value
            if "{" in val and "}" in val:
                return f'f{val!r}'
            return repr(val)

        if isinstance(expr, NumberLiteral):
            return str(expr.value)

        if isinstance(expr, BooleanLiteral):
            return "True" if expr.value else "False"

        if isinstance(expr, ListLiteral):
            items_str = ", ".join([self._emit_expression(it) for it in expr.items])
            return f"[{items_str}]"

        if isinstance(expr, Identifier):
            return expr.name

        if isinstance(expr, MemberAccessExpr):
            target_code = self._emit_expression(expr.target)
            return f"{target_code}.{expr.member}"

        if isinstance(expr, BinaryExpr):
            left = self._emit_expression(expr.left)
            right = self._emit_expression(expr.right)
            if expr.op == "contains":
                return f"({right} in {left})"
            return f"({left} {expr.op} {right})"

        if isinstance(expr, CallApiExpr):
            params_dict = "{" + ", ".join([f"{k!r}: {self._emit_expression(v)}" for k, v in expr.params.items()]) + "}"
            return f"await _call_api_{expr.api_name}({params_dict})"

        if isinstance(expr, FunctionCallExpr):
            args_codes = [self._emit_expression(a) for a in expr.args]
            all_args = ["_msg_target", "_user=user"] + args_codes
            return f"await {expr.func_name}({', '.join(all_args)})"

        return "None"

    def _emit_runner_functions(self) -> list[str]:
        lines = [
            "def create_bot(token: str) -> tuple[Bot, Dispatcher]:",
            "    bot = Bot(token=token)",
            "    dp = Dispatcher()",
            "    dp.include_router(router)",
            "    return bot, dp",
            "",
            "async def run_bot(token: str) -> None:",
            "    await _init_database()",
            "    bot, dp = create_bot(token)",
        ]

        if self.schedulers:
            lines.append("    asyncio.create_task(_run_tele_schedulers(bot))")

        if self.mode == "webhook":
            lines.extend([
                f"    logger.info('Запуск бота %r в режиме webhook на порту %s...', {self.bot_name!r}, {self.webhook_port})",
                "    from aiohttp import web",
                "    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application",
                f"    await bot.set_webhook({self.webhook_url!r})",
                "    app = web.Application()",
                "    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)",
                "    webhook_requests_handler.register(app, path='/telegram/webhook')",
                "    setup_application(app, dp, bot=bot)",
                f"    runner = web.AppRunner(app)",
                "    await runner.setup()",
                f"    site = web.TCPSite(runner, '0.0.0.0', {self.webhook_port})",
                "    await site.start()",
                "    while True:",
                "        await asyncio.sleep(3600)",
            ])
        else:
            lines.extend([
                f"    logger.info('Запуск бота %r в режиме %r...', {self.bot_name!r}, {self.mode!r})",
                "    await dp.start_polling(bot)",
            ])

        lines.extend([
            "",
            "if __name__ == '__main__':",
            "    token = os.environ.get('BOT_TOKEN', '')",
            "    if not token:",
            "        logger.error('Переменная окружения BOT_TOKEN не найдена.')",
            "        sys.exit(1)",
            "    try:",
            "        asyncio.run(run_bot(token))",
            "    except (KeyboardInterrupt, SystemExit):",
            "        logger.info('Работа бота остановлена.')",
            "",
        ])
        return lines

    def _emit_locales_layer(self, loc: LocalesDecl) -> list[str]:
        lines = [
            f"_LOCALES = {loc.translations!r}",
            "",
            "def t(key: str, lang: str = 'ru') -> str:",
            "    # Перевод по ключу с fallback на первый доступный язык",
            "    if lang in _LOCALES and key in _LOCALES[lang]:",
            "        return _LOCALES[lang][key]",
            "    for l_dict in _LOCALES.values():",
            "        if key in l_dict:",
            "            return l_dict[key]",
            "    return key",
        ]
        return lines

    def _emit_ai_client(self, ai: AiDecl) -> list[str]:
        model = ai.config.get("model", "gpt-4o-mini")
        key_name = ai.config.get("key", "OPENAI_API_KEY")
        base_url = ai.config.get("url", "https://api.openai.com/v1/chat/completions")
        lines = [
            f"async def _ask_ai_{ai.name}(prompt: str) -> str:",
            f"    api_key = os.environ.get({key_name!r}, '')",
            f"    headers = {{'Authorization': f'Bearer {{api_key}}', 'Content-Type': 'application/json'}}",
            f"    payload = {{'model': {model!r}, 'messages': [{{'role': 'user', 'content': prompt}}]}}",
            f"    async with aiohttp.ClientSession() as session:",
            f"        async with session.post({base_url!r}, json=payload, headers=headers) as resp:",
            f"            if resp.status == 200:",
            f"                data = await resp.json()",
            f"                return data['choices'][0]['message']['content']",
            f"            return f'AI Error: {{resp.status}}'",
            "",
            f"async def _stream_ai_{ai.name}(prompt: str):",
            f"    # Потоковый генератор чанков",
            f"    full_resp = await _ask_ai_{ai.name}(prompt)",
            f"    words = full_resp.split(' ')",
            f"    for i in range(0, len(words), 3):",
            f"        yield ' '.join(words[i:i+3]) + ' '",
            f"        await asyncio.sleep(0.08)",
        ]
        return lines

    def _emit_antispam_middleware(self, antispam: AntispamDecl) -> list[str]:
        lines = [
            "class _AntispamMiddleware:",
            "    def __init__(self):",
            f"        self.limit = {antispam.limit}",
            f"        self.per = {antispam.per_seconds}",
            f"        self.action = {antispam.action!r}",
            "        self.user_records = {}",
            "",
            "    async def __call__(self, handler, event, data):",
            "        from_user = getattr(event, 'from_user', None)",
            "        if not from_user:",
            "            return await handler(event, data)",
            "        uid = from_user.id",
            "        now = time.time()",
            "        timestamps = self.user_records.get(uid, [])",
            "        timestamps = [t for t in timestamps if now - t < self.per]",
            "        if len(timestamps) >= self.limit:",
            "            if self.action == 'warn':",
            "                await event.answer('⚠️ Слишком много сообщений! Подождите.')",
            "            return",
            "        timestamps.append(now)",
            "        self.user_records[uid] = timestamps",
            "        return await handler(event, data)",
            "",
            "router.message.middleware(_AntispamMiddleware())",
        ]
        return lines

    def _emit_special_hook(self, hook: HookDecl, index: int) -> list[str]:
        lines = []
        if hook.hook_type == "on_payment":
            func_name = f"_handle_payment_{index}"
            lines = [
                "@router.message(F.successful_payment)",
                f"async def {func_name}(message: types.Message, state: FSMContext = None):",
                "    _msg_target = message",
                "    user = _CtxUser(message.from_user)",
                "    user.coins = await _get_user_db(user.id, 'coins', 0)",
                "    chat = _CtxChat(message.chat)",
            ]
            body = self._emit_block(hook.body, indent=4)
            lines.extend(body if body else ["    pass"])

        elif hook.hook_type == "on_join_request":
            func_name = f"_handle_join_req_{index}"
            lines = [
                "@router.chat_join_request()",
                f"async def {func_name}(request: types.ChatJoinRequest):",
                "    user = _CtxUser(request.from_user)",
                "    chat = _CtxChat(request.chat)",
                "    _msg_target = request",
            ]
            # approve / decline трансляция
            for stmt in hook.body.statements:
                if isinstance(stmt, ExprStmt) and isinstance(stmt.expr, Identifier):
                    if stmt.expr.name == "approve":
                        lines.append("    await request.approve()")
                    elif stmt.expr.name == "decline":
                        lines.append("    await request.decline()")
            if not lines[-1].startswith("    await"):
                lines.append("    pass")

        elif hook.hook_type == "on_poll_answer":
            func_name = f"_handle_poll_answer_{index}"
            lines = [
                "@router.poll_answer()",
                f"async def {func_name}(answer: types.PollAnswer):",
                "    user = _CtxUser(answer.user)",
                "    _msg_target = answer",
            ]
            body = self._emit_block(hook.body, indent=4)
            lines.extend(body if body else ["    pass"])

        return lines

    def _emit_inline_query(self, iq: InlineQueryDecl, index: int) -> list[str]:
        func_name = f"_handle_inline_{index}"
        lines = [
            "@router.inline_query()",
            f"async def {func_name}(query: types.InlineQuery):",
            "    results = []",
        ]
        for idx, res in enumerate(iq.results):
            t_code = self._emit_expression(res.title)
            c_code = self._emit_expression(res.content)
            lines.append(f"    results.append(types.InlineQueryResultArticle(")
            lines.append(f"        id='res_{idx}',")
            lines.append(f"        title={t_code},")
            lines.append(f"        input_message_content=types.InputTextMessageContent(message_text={c_code})")
            lines.append(f"    ))")
        lines.append("    await query.answer(results, is_personal=True, cache_time=5)")
        return lines

    def _emit_scheduler_tasks(self) -> list[str]:
        lines = [
            "async def _run_tele_schedulers(bot: Bot):",
            "    # Фоновый планировщик TeleLang",
        ]
        for idx, sch in enumerate(self.schedulers):
            sec = sch.interval_value * 60 if "minute" in sch.interval_unit else (sch.interval_value * 3600 if "hour" in sch.interval_unit else sch.interval_value)
            task_fn = f"_task_{idx}"
            lines.append(f"    async def {task_fn}():")
            lines.append("        while True:")
            lines.append(f"            await asyncio.sleep({sec})")
            lines.append("            try:")
            # Создаем фейковый _msg_target для работы send / broadcast
            lines.append("                class _FakeTarget:")
            lines.append("                    def __init__(self, b): self.bot = b")
            lines.append("                _msg_target = _FakeTarget(bot)")
            body = self._emit_block(sch.body, indent=16)
            lines.extend(body if body else ["                pass"])
            lines.append("            except Exception as e:")
            lines.append("                logger.error(f'Ошибка планировщика: {e}')")
            lines.append(f"    asyncio.create_task({task_fn}())")
        return lines
