"""Тесты лексера для конструкций Этапа 2."""

import unittest
from telelang.lexer.lexer import Lexer
from telelang.lexer.tokens import TokenType


class TestLexerStage2(unittest.TestCase):
    def test_stage2_tokens(self):
        code = '''
        if coins > 50 {
            send "Много"
        } else {
            send "Мало"
        }

        buttons {
            "Профиль" -> profile()
            "Сайт" -> url("https://example.com")
        }

        on message {
            if message.text contains "ping" {
                send "pong"
            }
        }
        '''
        tokens = Lexer(code).tokenize()
        types = [t.type for t in tokens]

        self.assertIn(TokenType.IF, types)
        self.assertIn(TokenType.ELSE, types)
        self.assertIn(TokenType.GT, types)
        self.assertIn(TokenType.BUTTONS, types)
        self.assertIn(TokenType.ARROW, types)
        self.assertIn(TokenType.ON, types)
        self.assertIn(TokenType.MESSAGE, types)
        self.assertIn(TokenType.CONTAINS, types)
        self.assertIn(TokenType.DOT, types)
        self.assertIn(TokenType.LPAREN, types)
        self.assertIn(TokenType.RPAREN, types)

    def test_comparison_operators(self):
        code = "== != < > <= >="
        tokens = Lexer(code).tokenize()
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        expected = [
            TokenType.EQEQ,
            TokenType.NOT_EQ,
            TokenType.LT,
            TokenType.GT,
            TokenType.LTE,
            TokenType.GTE,
        ]
        self.assertEqual(types, expected)


if __name__ == "__main__":
    unittest.main()
