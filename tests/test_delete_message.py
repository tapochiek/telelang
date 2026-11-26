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


BODY = 'on message { if message.text == "спам" { delete message } }'


class DeleteMessageTests(unittest.TestCase):
    def test_generated_action(self):
        for mode in ("bot", "userbot"):
            with self.subTest(mode=mode):
                _, code = TeleCompiler.compile_source(f'{mode} "Test" {{}} ' + BODY)
                compile(code, "<generated>", "exec")
                handler = next(node for node in ast.parse(code).body
                               if getattr(node, "name", "") == "_handle_on_message_0")
                # Exercise the emitted conditional and its SDK call without a Telegram session.
                handler.decorator_list.clear()
                handler.args = ast.parse("def run(message, _msg_target, _event): pass").body[0].args
                handler.body = [handler.body[-1]]
                namespace = {}
                exec(compile(ast.Module([handler], []), "<handler>", "exec"), namespace)
                current = SimpleNamespace(delete=AsyncMock())
                for text in ("привет", "спам"):
                    asyncio.run(namespace[handler.name](SimpleNamespace(text=text), current,
                                                        SimpleNamespace(message=current)))
                    self.assertEqual(current.delete.await_count, int(text == "спам"))

    def test_mock_command(self):
        with TemporaryDirectory() as directory:
            file = Path(directory) / "bot.tl"
            file.write_text('bot "Test" {} command "/clean" { delete message }', encoding="utf-8")
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(MockRunner(file).handle_input("/clean"), [])
            self.assertIn("удалено текущее сообщение", output.getvalue())

    def test_requires_current_message(self):
        with self.assertRaisesRegex(TeleLangSyntaxError, "delete message"):
            TeleCompiler.compile_source('bot "Test" {} every 10 minutes { delete message }')

    def test_delete_still_usable_as_a_name(self):
        TeleCompiler.compile_source('bot "Test" {} command "/test" { delete = 1 send delete }')
