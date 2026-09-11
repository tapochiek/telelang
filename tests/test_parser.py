"""Тесты синтаксического анализатора (Parser)."""

import unittest
from telelang.errors import TeleLangSyntaxError
from telelang.lexer.lexer import Lexer
from telelang.parser.ast_nodes import (
    Block,
    BotDecl,
    CommandDecl,
    Program,
    SendStmt,
    StringLiteral,
)
from telelang.parser.parser import Parser


class TestParser(unittest.TestCase):
    def _parse(self, code: str) -> Program:
        tokens = Lexer(code).tokenize()
        return Parser(tokens, source_code=code).parse()

    def test_parse_minimal_bot(self):
        code = '''
        bot "MyBot"

        command "/start" {
            send "Привет!"
        }
        '''
        prog = self._parse(code)
        self.assertIsInstance(prog, Program)
        self.assertEqual(len(prog.declarations), 2)

        bot_decl = prog.declarations[0]
        self.assertIsInstance(bot_decl, BotDecl)
        self.assertEqual(bot_decl.name, "MyBot")

        cmd_decl = prog.declarations[1]
        self.assertIsInstance(cmd_decl, CommandDecl)
        self.assertEqual(cmd_decl.command, "/start")
        self.assertEqual(len(cmd_decl.body.statements), 1)

        send_stmt = cmd_decl.body.statements[0]
        self.assertIsInstance(send_stmt, SendStmt)
        self.assertIsInstance(send_stmt.message, StringLiteral)
        self.assertEqual(send_stmt.message.value, "Привет!")

    def test_parse_bot_with_config(self):
        code = '''
        bot "MyBot" {
            mode = "polling"
            token = "123456:abc"
        }
        '''
        prog = self._parse(code)
        bot_decl = prog.declarations[0]
        self.assertIsInstance(bot_decl, BotDecl)
        self.assertEqual(bot_decl.config.get("mode"), "polling")
        self.assertEqual(bot_decl.config.get("token"), "123456:abc")

    def test_parse_top_level_token(self):
        code = '''
        token = "123456:secret_token"
        bot "MyBot"
        '''
        prog = self._parse(code)
        self.assertEqual(len(prog.declarations), 2)
        config_decl = prog.declarations[0]
        self.assertEqual(config_decl.key, "token")
        self.assertEqual(config_decl.value, "123456:secret_token")

    def test_missing_bot_name_error(self):
        code = 'bot 123'
        with self.assertRaises(TeleLangSyntaxError) as ctx:
            self._parse(code)
        self.assertIn("ожидается имя бота в кавычках", str(ctx.exception))

    def test_missing_command_brace_error(self):
        code = 'command "/start" send "Привет!" }'
        with self.assertRaises(TeleLangSyntaxError) as ctx:
            self._parse(code)
        self.assertIn("Ожидался символ '{'", str(ctx.exception))

    def test_unclosed_block_error(self):
        code = '''
        command "/start" {
            send "Привет!"
        '''
        with self.assertRaises(TeleLangSyntaxError) as ctx:
            self._parse(code)
        self.assertIn("Незакрытый блок: ожидался символ '}'", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
