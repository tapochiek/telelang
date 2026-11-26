"r""Тестовый движок (Mock Engine / Dry-Run) для команды tele test."""

from __future__ import annotations
import os
import operator
import random
import time
import sys
from pathlib import Path
from typing import Any, Optional
from telelang.compiler import TeleCompiler
from telelang.parser.ast_nodes import (
    BinaryExpr,
    CommandDecl,
    IfStmt,
    FunctionCallExpr,
    Identifier,
    MemberAccessExpr,
    StringLiteral,
    VariableAssignStmt,
    OnMessageDecl,
    DeleteMessageStmt,
    BanUserStmt,
    MuteUserStmt,
    KickUserStmt,
    PinMessageStmt,
    SendStmt,
    ButtonsBlock,
    SendMediaStmt,
    SendPollStmt,
    SendChecklistStmt,
    SendRichStmt,
    ReactStmt,
)


class MockRunner:
    """Локальный эмулятор Telegram-бота для интерактивного тестирования в терминале."""

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path).resolve()
        self.compiler = TeleCompiler()
        self.program, _ = self.compiler.compile_file(self.file_path)
        self.user_name = "Тестер"
        self.user_id = 99999999
        self.user_username = "test_user"

    def run_interactive(self) -> None:
        bot_name = "TeleBot"
        for decl in self.program.declarations:
            if hasattr(decl, "name") and type(decl).__name__ in ("BotDecl", "UserbotDecl"):
                bot_name = decl.name
                break

        print("=" * 60)
        print(f"  🤖 TeleLang DRY-RUN TEST: {bot_name}")
        print(f"  Пользователь: {self.user_name} (@{self.user_username}, id={self.user_id})")
        print("  Введите текст команды (например /start) или сообщение.")
        print("  Для выхода введите 'exit'.")
        print("=" * 60)

        while True:
            try:
                user_input = input("\nVy > ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n[Testing done]")
                break

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q"):
                print("\n[Testing done]")
                break

            if user_input.startswith(":webapp "):
                self.handle_webapp_data(user_input[len(":webapp "):])
            else:
                self.handle_input(user_input)

    def handle_webapp_data(self, data: str) -> list[str]:
        responses = []
        for decl in self.program.declarations:
            if isinstance(decl, OnMessageDecl) and decl.webapp_data:
                self._execute_block(decl.body, "", responses, {"webapp_data": data})
                break
        return responses

    def handle_input(self, text: str) -> list[str]:
        responses = []
        matched = False

        if text.startswith("/"):
            cmd_name = text.split()[0]
            for decl in self.program.declarations:
                if isinstance(decl, CommandDecl) and decl.command == cmd_name:
                    matched = True
                    self._execute_block(decl.body, text, responses)
                    break

        if not matched:
            for decl in self.program.declarations:
                if isinstance(decl, OnMessageDecl) and not decl.webapp_data:
                    matched = True
                    self._execute_block(decl.body, text, responses)
                    break

        if not matched:
            print("Bot > (no handler)")

        return responses

    def _execute_block(self, block, incoming_text: str, responses: list[str], variables=None) -> None:
        if variables is None:
            variables = {}
        for stmt in block.statements:
            if isinstance(stmt, DeleteMessageStmt):
                print("Bot > [удалено текущее сообщение]")
            elif isinstance(stmt, BanUserStmt):
                print(f"Bot > [бан пользователя {self.user_id}]")
            elif isinstance(stmt, MuteUserStmt):
                print(f"Bot > [мут пользователя {self.user_id} на {stmt.minutes} мин.]")
            elif isinstance(stmt, KickUserStmt):
                print(f"Bot > [кик пользователя {self.user_id}]")
            elif isinstance(stmt, PinMessageStmt):
                print("Bot > [закреплено текущее сообщение]")
            elif isinstance(stmt, SendStmt):
                msg = str(self._eval_value(stmt.message, incoming_text, variables))
                print(f"Bot > {msg}")
                responses.append(msg)

            elif isinstance(stmt, VariableAssignStmt):
                variables[stmt.name] = self._eval_value(stmt.value, incoming_text, variables)

            elif isinstance(stmt, IfStmt):
                condition = self._eval_value(stmt.condition, incoming_text, variables)
                branch = stmt.then_branch if condition else stmt.else_branch
                if branch is not None:
                    self._execute_block(branch, incoming_text, responses, variables)

            elif isinstance(stmt, ButtonsBlock):
                print("       [ Клавиатура: ]")
                for btn in stmt.buttons:
                    emoji = f"{btn.icon_emoji} " if btn.icon_emoji else ""
                    suffix = f" (Mini App: {btn.target.args[0].value})" if btn.is_webapp else ""
                    print(f"       🔘 [{emoji}{btn.label}]{suffix}")

            elif isinstance(stmt, SendMediaStmt):
                print(f"🤖 Бот > 📁 [Медиа: {stmt.media_type}] {stmt.file_path}")

            elif isinstance(stmt, SendPollStmt):
                q = getattr(stmt.question, "value", str(stmt.question))
                print(f"🤖 Бот > 📊 [Опрос] {q}")

            elif isinstance(stmt, SendChecklistStmt):
                t = getattr(stmt.title, "value", str(stmt.title))
                print(f"🤖 Бот > 📋 [Чек-лист: {t}]")
                for task in stmt.tasks:
                    print(f"         ⬜ {task}")

            elif isinstance(stmt, SendRichStmt):
                print("🤖 Бот > 📄 [Rich Message]")
                for blk in stmt.blocks:
                    print(f"         • {blk.get('type')}: {blk.get('text', blk.get('rows', ''))}")

            elif isinstance(stmt, ReactStmt):
                print("🤖 Бот > 👍 Поставил реакцию на сообщение")

    def _eval_value(self, expr, incoming_text: str, variables: dict):
        if isinstance(expr, BinaryExpr):
            left = self._eval_value(expr.left, incoming_text, variables)
            right = self._eval_value(expr.right, incoming_text, variables)
            operations = {
                "+": operator.add, "-": operator.sub, "*": operator.mul, "/": operator.truediv,
                "==": operator.eq, "!=": operator.ne, "<": operator.lt, ">": operator.gt,
                "<=": operator.le, ">=": operator.ge, "contains": operator.contains,
            }
            return operations[expr.op](left, right)
        if isinstance(expr, Identifier):
            return variables.get(expr.name, str(expr))
        if isinstance(expr, FunctionCallExpr) and expr.func_name == "random":
            low, high = (self._eval_value(arg, incoming_text, variables) for arg in expr.args)
            return random.randint(low, high)
        if isinstance(expr, MemberAccessExpr):
            if expr.is_time_now:
                return int(time.time())
            if expr.member in ("length", "lower", "upper"):
                value = self._eval_value(expr.target, incoming_text, variables)
                if expr.member == "length":
                    return str.__len__(value)
                return str.lower(value) if expr.member == "lower" else str.upper(value)
            if isinstance(expr.target, Identifier):
                field = (expr.target.name, expr.member)
                fields = {
                    ("message", "text"): incoming_text,
                    ("user", "id"): self.user_id,
                    ("user", "username"): self.user_username,
                    ("user", "name"): self.user_name,
                }
                if field in fields:
                    return fields[field]
        if not isinstance(expr, StringLiteral):
            return getattr(expr, "value", str(expr))
        val = expr.value
        val = val.replace("{user.name}", self.user_name)
        val = val.replace("{user.id}", str(self.user_id))
        val = val.replace("{user.username}", self.user_username)
        val = val.replace("{message.text}", incoming_text)
        if "webapp_data" in variables:
            val = val.replace("{webapp_data}", str(variables["webapp_data"]))
        return val
