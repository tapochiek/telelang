import __future__
import ast
import asyncio
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import AsyncMock

from telelang.compiler import TeleCompiler
from telelang.errors import TeleLangSyntaxError
from telelang.testing.mock_engine import MockRunner


def handler(mode, action):
    _, code = TeleCompiler.compile_source(f'{mode} "Test" {{}} on message {{ {action} }}')
    compile(code, "<generated>", "exec")
    nodes = ast.parse(code).body
    fn = next(n for n in nodes if getattr(n, "name", "") == "_handle_on_message_0")
    fn.decorator_list.clear()
    namespace = {"_get_user_db": AsyncMock(), "_CtxChat": lambda chat: chat,
                 "_CtxUser": lambda sender: SimpleNamespace(id=getattr(sender, "id", 0)),
                 "_CtxMsg": lambda event: event.message}
    exec(compile(ast.Module([fn], []), "<handler>", "exec", flags=__future__.annotations.compiler_flag), namespace)
    return namespace[fn.name]


class UserModerationTests(unittest.TestCase):
    def test_ban_bot(self):
        run = handler("bot", "ban user")
        api = AsyncMock()
        message = SimpleNamespace(bot=api, chat=SimpleNamespace(type="private", id=-10),
                                  from_user=SimpleNamespace(id=7), sender_chat=None)
        asyncio.run(run(message))
        message.chat.type = "supergroup"
        message.sender_chat = message.chat
        asyncio.run(run(message))
        api.ban_chat_member.assert_not_awaited()
        message.sender_chat = None
        asyncio.run(run(message))
        api.ban_chat_member.assert_awaited_once_with(chat_id=-10, user_id=7)

    def test_ban_userbot(self):
        run = handler("userbot", "ban user")
        event = SimpleNamespace(client=AsyncMock(), chat_id=-10, sender_id=7, is_group=True,
                                out=True, message=None, get_sender=AsyncMock())
        asyncio.run(run(event))
        event.out = False
        asyncio.run(run(event))
        event.client.edit_permissions.assert_awaited_once_with(-10, 7, view_messages=False)

    def test_ban_context(self):
        with self.assertRaisesRegex(TeleLangSyntaxError, "ban user"):
            TeleCompiler.compile_source('bot "Test" {} every 1 minutes { ban user }')
        TeleCompiler.compile_source('bot "Test" {} on message { ban = 1 send ban }')

    def test_ban_mock(self):
        with TemporaryDirectory() as directory:
            file = Path(directory) / "bot.tl"
            file.write_text('bot "Test" {} on message { ban user }', encoding="utf-8")
            runner = MockRunner(file)
            with redirect_stdout(io.StringIO()) as output:
                runner.handle_input("test")
            self.assertIn(f"бан пользователя {runner.user_id}", output.getvalue())
