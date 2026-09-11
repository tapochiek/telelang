"r""Тестовый движок (Mock Engine / Dry-Run) для команды tele test."""

from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Any, Optional
from telelang.compiler import TeleCompiler
from telelang.parser.ast_nodes import (
    CommandDecl,
    OnMessageDecl,
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

            self.handle_input(user_input)

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
                if isinstance(decl, OnMessageDecl):
                    matched = True
                    self._execute_block(decl.body, text, responses)
                    break

        if not matched:
            print("Bot > (no handler)")

        return responses

    def _execute_block(self, block, incoming_text: str, responses: list[str]) -> None:
        for stmt in block.statements:
            if isinstance(stmt, SendStmt):
                msg = self._eval_mock_text(stmt.message, incoming_text)
                print(f"Bot > {msg}")
                responses.append(msg)

            elif isinstance(stmt, ButtonsBlock):
                print("       [ Клавиатура: ]")
                for btn in stmt.buttons:
                    emoji = f"{btn.icon_emoji} " if btn.icon_emoji else ""
                    print(f"       🔘 [{emoji}{btn.label}]")

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

    def _eval_mock_text(self, expr, incoming_text: str) -> str:
        raw = getattr(expr, "value", str(expr))
        val = str(raw)
        val = val.replace("{user.name}", self.user_name)
        val = val.replace("{user.id}", str(self.user_id))
        val = val.replace("{user.username}", self.user_username)
        val = val.replace("{message.text}", incoming_text)
        return val
