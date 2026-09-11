"""Тесты семантического анализатора для Этапа 2."""

import unittest
from telelang.errors import TeleLangSemanticError
from telelang.lexer.lexer import Lexer
from telelang.parser.parser import Parser
from telelang.semantic.analyzer import SemanticAnalyzer


class TestSemanticStage2(unittest.TestCase):
    def _analyze(self, code: str):
        tokens = Lexer(code).tokenize()
        prog = Parser(tokens, source_code=code).parse()
        analyzer = SemanticAnalyzer(source_code=code)
        analyzer.analyze(prog)
        return analyzer

    def test_buttons_forbidden_in_userbot(self):
        code = '''
        userbot "MyUserbot"
        command "/menu" {
            buttons {
                "Кнопка" -> click()
            }
        }
        '''
        with self.assertRaises(TeleLangSemanticError) as ctx:
            self._analyze(code)
        self.assertIn("недоступен в режиме 'userbot'", str(ctx.exception))

    def test_duplicate_function_name(self):
        code = '''
        bot "MyBot"
        function test() { send "1" }
        function test() { send "2" }
        '''
        with self.assertRaises(TeleLangSemanticError) as ctx:
            self._analyze(code)
        self.assertIn("Повторное объявление функции 'test'", str(ctx.exception))

    def test_duplicate_function_params(self):
        code = '''
        bot "MyBot"
        function test(x, x) { send "1" }
        '''
        with self.assertRaises(TeleLangSemanticError) as ctx:
            self._analyze(code)
        self.assertIn("Дублирующийся параметр 'x'", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
