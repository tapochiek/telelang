import ast
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from telelang.testing.mock_engine import MockRunner
from telelang.codegen.project_emitter import ProjectEmitter
from telelang.codegen.python_emitter import PythonEmitter
from telelang.compiler import TeleCompiler
from telelang.errors import TeleLangSemanticError, TeleLangSyntaxError


class WebAppButtonTests(unittest.TestCase):
    def test_reply_keyboard(self):
        source = 'bot "App" {} command "/app" { send "Open" buttons { "Shop" -> webapp("https://example.org") } }'
        prog, code = TeleCompiler.compile_source(source)
        ast.parse(code)
        emitter = PythonEmitter(prog)
        buttons = prog.declarations[-1].body.statements[-1]
        sdk = SimpleNamespace(KeyboardButton=SimpleNamespace, WebAppInfo=SimpleNamespace,
                              ReplyKeyboardMarkup=SimpleNamespace)
        env = {"types": sdk}
        exec("\n".join(emitter._emit_keyboard_builder(buttons, 0)), env)
        button = env["_keyboard"].keyboard[0][0]
        self.assertEqual((button.text, button.web_app.url), ("Shop", "https://example.org"))
        self.assertEqual(emitter.callbacks, [])

    def test_invalid_keyboard(self):
        for target in ('webapp()', 'webapp("http://example.org")', 'webapp("https://")',
                       'webapp("https://example.org") "Help" -> help()'):
            with self.subTest(target=target), self.assertRaises(TeleLangSyntaxError):
                TeleCompiler.compile_source('bot "App" {} command "/app" { buttons { "Open" -> ' + target + ' } }')

    def test_userbot_rejected(self):
        with self.assertRaises(TeleLangSemanticError):
            TeleCompiler.compile_source('userbot "App" {} on message { buttons { "Open" -> webapp("https://example.org") } }')


class WebAppDataTests(unittest.TestCase):
    source = ('bot "App" {} on message { send "обычное" } '
              'on webapp_data { if webapp_data == "catalog" { send "каталог" } else { send webapp_data } }')

    def test_routing_and_payload(self):
        _, code = TeleCompiler.compile_source(self.source)
        compile(code, "<bot>", "exec")
        self.assertIn("@router.message(~F.web_app_data)", code)
        self.assertIn("@router.message(F.web_app_data)", code)
        self.assertIn("webapp_data = message.web_app_data.data", code)
        _, old = TeleCompiler.compile_source('bot "App" {} on message { send "ok" }')
        self.assertIn("@router.message()", old)

    def test_mock_events(self):
        with TemporaryDirectory() as directory:
            file = Path(directory) / "main.tl"
            file.write_text(self.source, encoding="utf-8")
            runner = MockRunner(file)
            self.assertEqual(runner.handle_input("catalog"), ["обычное"])
            self.assertEqual(runner.handle_webapp_data("catalog"), ["каталог"])
            self.assertEqual(runner.handle_webapp_data('{"x":1}'), ['{"x":1}'])

    def test_modular_routing(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "main.tl").write_text('bot "App" {} import "events.tl" on message { send "ok" }')
            (root / "events.tl").write_text('on webapp_data { send webapp_data }')
            output = ProjectEmitter(root, root / "build").emit_project()
            self.assertIn("@router.message(~F.web_app_data)", (output / "main.py").read_text())
            self.assertIn("@router.message(F.web_app_data)", (output / "events.py").read_text())

    def test_userbot_rejected(self):
        with self.assertRaisesRegex(TeleLangSemanticError, "on webapp_data"):
            TeleCompiler.compile_source('userbot "App" {} on webapp_data { send webapp_data }')
