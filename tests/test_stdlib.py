import __future__
import ast
import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from telelang.compiler import TeleCompiler
from telelang.errors import TeleLangSyntaxError
from telelang.testing.mock_engine import MockRunner


BODY = """
on message {
    low = 1
    roll = random(low, 3 + 3)
    if roll == 6 { send roll }
    send random(4, 4)
    send message.text.lower
    send message.text.upper.length
    send "".length
    send time.now
    send time.now - time.now
}
"""
EXPECTED = ["6", "4", "ёжß🙂", "5", "0", "1700000000", "0"]


class TestStdlib(unittest.TestCase):
    def test_generated_handlers(self):
        for mode in ("bot", "userbot"):
            with self.subTest(mode=mode):
                _, code = TeleCompiler.compile_source(f'{mode} "Std" {{}}' + BODY)
                tree = ast.parse(code)
                compile(tree, "<generated>", "exec")
                # Run the generated handler and context classes without a Telegram session.
                selected = []
                for node in tree.body:
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        if node.names[0].asname in ("_tl_builtin", "_tl_randint", "_tl_clock"):
                            selected.append(node)
                    elif isinstance(node, ast.ClassDef) and node.name.startswith("_Ctx"):
                        selected.append(node)
                    elif isinstance(node, ast.AsyncFunctionDef) and node.name == "_handle_on_message_0":
                        node.decorator_list.clear()
                        selected.append(node)
                namespace = {"_get_user_db": AsyncMock(return_value=0)}
                with patch("random.randint", side_effect=lambda low, high: high) as randint, \
                     patch("time.time", return_value=1700000000.75):
                    program = ast.Module(body=selected, type_ignores=[])
                    exec(compile(program, "<handler>", "exec", flags=__future__.annotations.compiler_flag), namespace)
                    reply = AsyncMock()
                    event = SimpleNamespace(text="Ёжß🙂", raw_text="Ёжß🙂", id=1, chat=None,
                                            from_user=None, answer=reply, respond=reply,
                                            get_sender=AsyncMock(return_value=None))
                    asyncio.run(namespace["_handle_on_message_0"](event))
                    self.assertEqual([call.args[0] for call in reply.await_args_list], EXPECTED)
                    self.assertEqual([call.args for call in randint.call_args_list], [(1, 6), (4, 4)])

    def test_mock_runner(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "std.tl"
            source.write_text('bot "Std" {}' + BODY, encoding="utf-8")
            with patch("random.randint", side_effect=lambda low, high: high), \
                 patch("time.time", return_value=1700000000.75):
                self.assertEqual(MockRunner(source).handle_input("Ёжß🙂"), EXPECTED)

    def test_invalid_syntax(self):
        for expr in ("random()", "random(1)", "random(1, 2, 3)", '"x".upper()', 'time.now()'):
            with self.subTest(expr=expr), self.assertRaises(TeleLangSyntaxError):
                TeleCompiler.compile_source('bot "Std" {} on message { send ' + expr + ' }')
