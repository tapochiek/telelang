"""Генератор кода для режима userbot на базе Telethon (MTProto)."""

from __future__ import annotations
from pathlib import Path
from typing import Any, Optional
from telelang.parser.ast_nodes import (
    BinaryExpr,
    Block,
    BooleanLiteral,
    CommandDecl,
    Expr,
    ExprStmt,
    FunctionCallExpr,
    FunctionDecl,
    Identifier,
    IfStmt,
    MemberAccessExpr,
    NumberLiteral,
    OnMessageDecl,
    Program,
    SendStmt,
    Stmt,
    StringLiteral,
    UserbotDecl,
    VariableAssignStmt,
)


class TelethonEmitter:
    """Транслирует AST-дерево TeleLang в код юзербота на базе Telethon."""

    def __init__(self, program: Program):
        self.program = program
        self.userbot_name: str = "MyUserbot"
        self.api_id: Optional[int] = None
        self.api_hash: Optional[str] = None
        self.session: str = "my_session"
        self.commands: list[CommandDecl] = []
        self.on_messages: list[OnMessageDecl] = []
        self.functions: list[FunctionDecl] = []

    def emit(self) -> str:
        """Генерирует полный Python-код для Telethon."""
        for decl in self.program.declarations:
            if isinstance(decl, UserbotDecl):
                self.userbot_name = decl.name
                self.api_id = decl.config.get("api_id")
                self.api_hash = decl.config.get("api_hash")
                self.session = decl.config.get("session", f"sessions/{decl.name.lower()}")
            elif isinstance(decl, CommandDecl):
                self.commands.append(decl)
            elif isinstance(decl, OnMessageDecl):
                self.on_messages.append(decl)
            elif isinstance(decl, FunctionDecl):
                self.functions.append(decl)

        api_id_val = repr(self.api_id) if self.api_id else "int(os.environ.get('TELEGRAM_API_ID', 0))"
        api_hash_val = repr(self.api_hash) if self.api_hash else "os.environ.get('TELEGRAM_API_HASH', '')"
        session_val = repr(self.session)

        lines: list[str] = [
            "# -*- coding: utf-8 -*-",
            "# Сгенерировано компилятором TeleLang (Userbot / Telethon). Не редактируйте вручную.",
            "import asyncio",
            "import logging",
            "import os",
            "import sys",
            "from pathlib import Path",
            "from telethon import TelegramClient, events",
            "",
            "logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')",
            f"logger = logging.getLogger({self.userbot_name!r})",
            "",
            f"api_id = {api_id_val}",
            f"api_hash = {api_hash_val}",
            f"session_path = {session_val}",
            "Path(session_path).parent.mkdir(parents=True, exist_ok=True)",
            "client = TelegramClient(session_path, api_id, api_hash)",
            "",
            "# Контекстные классы для юзербота",
            "class _CtxUser:",
            "    def __init__(self, sender):",
            "        self.id = sender.id if sender else 0",
            "        first_name = getattr(sender, 'first_name', '') or ''",
            "        last_name = getattr(sender, 'last_name', '') or ''",
            "        self.name = f'{first_name} {last_name}'.strip()",
            "        self.username = getattr(sender, 'username', '') or ''",
            "        self.is_premium = bool(getattr(sender, 'premium', False))",
            "    def __str__(self):",
            "        return self.name",
            "",
            "class _CtxMsg:",
            "    def __init__(self, event):",
            "        self.id = event.id if event else 0",
            "        self.text = event.raw_text or ''",
            "    def __str__(self):",
            "        return self.text",
            "",
        ]

        # 1. Функции
        for fn in self.functions:
            lines.extend(self._emit_function(fn))
            lines.append("")

        # 2. Обработчики команд
        for idx, cmd in enumerate(self.commands):
            lines.extend(self._emit_command(cmd, idx))
            lines.append("")

        # 3. Обработчики on message
        for idx, on_msg in enumerate(self.on_messages):
            lines.extend(self._emit_on_message(on_msg, idx))
            lines.append("")

        # 4. Запуск юзербота
        lines.extend(self._emit_runner())
        return "\n".join(lines)

    def _emit_function(self, fn: FunctionDecl) -> list[str]:
        param_list = ["_event=None"] + fn.params
        params_str = ", ".join(param_list)

        lines = [
            f"async def {fn.name}({params_str}):",
            "    sender = await _event.get_sender() if _event else None",
            "    user = _CtxUser(sender)",
            "    message = _CtxMsg(_event)",
        ]
        body = self._emit_block(fn.body, indent=4)
        lines.extend(body if body else ["    pass"])
        return lines

    def _emit_command(self, cmd: CommandDecl, index: int) -> list[str]:
        clean_cmd = cmd.command.lstrip("/")
        func_name = f"_handle_cmd_{clean_cmd}_{index}"
        pattern = rf"^/{clean_cmd}(?:\s+.*)?$"

        lines = [
            f"@client.on(events.NewMessage(pattern={pattern!r}))",
            f"async def {func_name}(event):",
            "    _event = event",
            "    sender = await event.get_sender()",
            "    user = _CtxUser(sender)",
            "    message = _CtxMsg(event)",
        ]
        body = self._emit_block(cmd.body, indent=4)
        lines.extend(body if body else ["    pass"])
        return lines

    def _emit_on_message(self, on_msg: OnMessageDecl, index: int) -> list[str]:
        func_name = f"_handle_on_message_{index}"

        lines = [
            "@client.on(events.NewMessage)",
            f"async def {func_name}(event):",
            "    _event = event",
            "    sender = await event.get_sender()",
            "    user = _CtxUser(sender)",
            "    message = _CtxMsg(event)",
        ]
        body = self._emit_block(on_msg.body, indent=4)
        lines.extend(body if body else ["    pass"])
        return lines

    def _emit_block(self, block: Block, indent: int = 4) -> list[str]:
        lines: list[str] = []
        pad = " " * indent

        for stmt in block.statements:
            if isinstance(stmt, SendStmt):
                msg_code = self._emit_expression(stmt.message)
                lines.append(f"{pad}await _event.respond({msg_code})")
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

        if isinstance(expr, FunctionCallExpr):
            args_codes = [self._emit_expression(a) for a in expr.args]
            all_args = ["_event"] + args_codes
            return f"await {expr.func_name}({', '.join(all_args)})"

        return "None"

    def _emit_runner(self) -> list[str]:
        lines = [
            "async def run_userbot():",
            f"    logger.info('Запуск юзербота %r (Telethon MTProto)...', {self.userbot_name!r})",
            "    await client.start()",
            "    logger.info('Юзербот успешно подключён к Telegram!')",
            "    await client.run_until_disconnected()",
            "",
            "if __name__ == '__main__':",
            "    try:",
            "        asyncio.run(run_userbot())",
            "    except (KeyboardInterrupt, SystemExit):",
            "        logger.info('Юзербот остановлен.')",
            "",
        ]
        return lines
