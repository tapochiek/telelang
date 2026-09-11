"""Тесты лексического анализатора (Lexer)."""

import unittest
from telelang.errors import TeleLangSyntaxError
from telelang.lexer.lexer import Lexer
from telelang.lexer.tokens import TokenType


class TestLexer(unittest.TestCase):
    def test_tokenize_basic(self):
        code = '''
        bot "MyBot"
        command "/start" {
            send "Привет!"
        }
        '''
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        types = [t.type for t in tokens]
        expected = [
            TokenType.BOT,
            TokenType.STRING,
            TokenType.COMMAND,
            TokenType.STRING,
            TokenType.LBRACE,
            TokenType.SEND,
            TokenType.STRING,
            TokenType.RBRACE,
            TokenType.EOF,
        ]
        self.assertEqual(types, expected)
        self.assertEqual(tokens[1].value, "MyBot")
        self.assertEqual(tokens[3].value, "/start")
        self.assertEqual(tokens[6].value, "Привет!")

    def test_comments_and_whitespace(self):
        code = '''
        # Это комментарий
        bot "TestBot" # Ещё комментарий
        '''
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        types = [t.type for t in tokens]
        self.assertEqual(types, [TokenType.BOT, TokenType.STRING, TokenType.EOF])

    def test_string_escapes(self):
        code = r'send "Строка с \"кавычками\" и \n переносом"'
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        self.assertEqual(tokens[1].value, 'Строка с "кавычками" и \n переносом')

    def test_unclosed_string_raises_syntax_error(self):
        code = 'bot "Unclosed'
        lexer = Lexer(code)
        with self.assertRaises(TeleLangSyntaxError) as ctx:
            lexer.tokenize()
        self.assertIn("Незакрытая строковая константа", str(ctx.exception))
        self.assertEqual(ctx.exception.span.line, 1)

    def test_unexpected_char(self):
        code = 'bot "Test" @'
        lexer = Lexer(code)
        with self.assertRaises(TeleLangSyntaxError) as ctx:
            lexer.tokenize()
        self.assertIn("Неожиданный символ: '@'", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
