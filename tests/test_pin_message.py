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


class PinMessageTests(unittest.TestCase):
    def test_compiled_handler(self):
        for mode in ("bot", "userbot"):
            with self.subTest(mode=mode):
                _, code = TeleCompiler.compile_source(
                    f'{mode} "Pin" {{}} on message {{ if user.id == 7 {{ pin message }} }}'
                )
                nodes = ast.parse(code).body
                handler = next(n for n in nodes if getattr(n, "name", "") == "_handle_on_message_0")
                handler.decorator_list.clear()
                context = {"_get_user_db": AsyncMock(), "_CtxChat": lambda chat: chat,
                           "_CtxUser": lambda user: user, "_CtxMsg": lambda event: event.message}
                exec(compile(ast.Module([handler], []), "<handler>", "exec",
                             flags=__future__.annotations.compiler_flag), context)
                message = SimpleNamespace(chat=None, pin=AsyncMock())
                for user_id in (99, 7):
                    message.from_user = SimpleNamespace(id=user_id)
                    event = SimpleNamespace(message=message, get_sender=AsyncMock(return_value=message.from_user))
                    asyncio.run(context[handler.name](message if mode == "bot" else event))
                    if user_id == 99:
                        message.pin.assert_not_awaited()
                if mode == "bot":
                    message.pin.assert_awaited_once_with(disable_notification=True)
                else:
                    message.pin.assert_awaited_once_with(notify=False)

    def test_mock_command(self):
        with TemporaryDirectory() as directory:
            file = Path(directory) / "bot.tl"
            file.write_text('bot "Pin" {} command "/pin" { pin message }', encoding="utf-8")
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(MockRunner(file).handle_input("/pin"), [])
            self.assertIn("закреплено текущее сообщение", output.getvalue())

    def test_context_and_identifier(self):
        with self.assertRaisesRegex(TeleLangSyntaxError, "pin message"):
            TeleCompiler.compile_source('bot "Pin" {} every 1 minutes { pin message }')
        TeleCompiler.compile_source('bot "Pin" {} on message { pin = 1 send pin }')
