"""Тесты семантического анализатора (SemanticAnalyzer)."""

import unittest
from telelang.errors import TeleLangSemanticError
from telelang.lexer.lexer import Lexer
from telelang.parser.parser import Parser
from telelang.semantic.analyzer import SemanticAnalyzer


class TestSemantic(unittest.TestCase):
    def _analyze(self, code: str):
        tokens = Lexer(code).tokenize()
        prog = Parser(tokens, source_code=code).parse()
        analyzer = SemanticAnalyzer(source_code=code)
        analyzer.analyze(prog)
        return analyzer

    def test_valid_bot(self):
        code = '''
        bot "ValidBot"
        command "/start" {
            send "Привет!"
        }
        '''
        analyzer = self._analyze(code)
        self.assertIsNotNone(analyzer.bot_decl)
        self.assertEqual(len(analyzer.commands), 1)

    def test_missing_bot_or_userbot(self):
        code = '''
        command "/start" {
            send "Привет!"
        }
        '''
        with self.assertRaises(TeleLangSemanticError) as ctx:
            self._analyze(code)
        self.assertIn("не найдено объявление бота ('bot') или юзербота ('userbot')", str(ctx.exception))

    def test_bot_and_userbot_conflict(self):
        code = '''
        bot "MyBot"
        userbot "MyUserbot"
        '''
        with self.assertRaises(TeleLangSemanticError) as ctx:
            self._analyze(code)
        self.assertIn("не может одновременно содержать объявление и 'bot', и 'userbot'", str(ctx.exception))

    def test_duplicate_bot_error(self):
        code = '''
        bot "Bot1"
        bot "Bot2"
        '''
        with self.assertRaises(TeleLangSemanticError) as ctx:
            self._analyze(code)
        self.assertIn("Повторное объявление бота", str(ctx.exception))

    def test_command_without_slash(self):
        code = '''
        bot "MyBot"
        command "start" {
            send "Привет!"
        }
        '''
        with self.assertRaises(TeleLangSemanticError) as ctx:
            self._analyze(code)
        self.assertIn("должно начинаться с символа '/'", str(ctx.exception))

    def test_invalid_bot_mode(self):
        code = '''
        bot "MyBot" {
            mode = "fast"
        }
        '''
        with self.assertRaises(TeleLangSemanticError) as ctx:
            self._analyze(code)
        self.assertIn("Недопустимый режим работы бота: 'fast'", str(ctx.exception))

    def test_webhook_without_url(self):
        code = '''
        bot "MyBot" {
            mode = "webhook"
        }
        '''
        with self.assertRaises(TeleLangSemanticError) as ctx:
            self._analyze(code)
        self.assertIn("необходимо указать 'webhook_url'", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
