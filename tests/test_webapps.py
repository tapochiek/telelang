import ast
import unittest
from types import SimpleNamespace

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
