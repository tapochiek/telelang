"""Тесты парсера для конструкций Этапа 2."""

import unittest
from telelang.lexer.lexer import Lexer
from telelang.parser.ast_nodes import (
    BinaryExpr,
    ButtonsBlock,
    FunctionCallExpr,
    FunctionDecl,
    IfStmt,
    MemberAccessExpr,
    OnMessageDecl,
    Program,
    VariableAssignStmt,
)
from telelang.parser.parser import Parser


class TestParserStage2(unittest.TestCase):
    def _parse(self, code: str) -> Program:
        tokens = Lexer(code).tokenize()
        return Parser(tokens, source_code=code).parse()

    def test_parse_if_else(self):
        code = '''
        bot "TestBot"
        command "/test" {
            if coins > 50 {
                send "Много"
            } else {
                send "Мало"
            }
        }
        '''
        prog = self._parse(code)
        cmd = prog.declarations[1]
        self.assertEqual(len(cmd.body.statements), 1)
        if_stmt = cmd.body.statements[0]
        self.assertIsInstance(if_stmt, IfStmt)
        self.assertIsInstance(if_stmt.condition, BinaryExpr)
        self.assertEqual(if_stmt.condition.op, ">")
        self.assertIsNotNone(if_stmt.else_branch)

    def test_parse_function_decl(self):
        code = '''
        bot "TestBot"
        function greet(name, age) {
            send "Привет, {name}!"
        }
        '''
        prog = self._parse(code)
        fn_decl = prog.declarations[1]
        self.assertIsInstance(fn_decl, FunctionDecl)
        self.assertEqual(fn_decl.name, "greet")
        self.assertEqual(fn_decl.params, ["name", "age"])

    def test_parse_buttons(self):
        code = '''
        bot "TestBot"
        command "/menu" {
            send "Выбери:"
            buttons {
                "Профиль" -> profile()
                "Сайт" -> url("https://example.com")
            }
        }
        '''
        prog = self._parse(code)
        cmd = prog.declarations[1]
        buttons_block = cmd.body.statements[1]
        self.assertIsInstance(buttons_block, ButtonsBlock)
        self.assertEqual(len(buttons_block.buttons), 2)
        self.assertEqual(buttons_block.buttons[0].label, "Профиль")
        self.assertIsInstance(buttons_block.buttons[0].target, FunctionCallExpr)
        self.assertEqual(buttons_block.buttons[1].label, "Сайт")

    def test_parse_on_message(self):
        code = '''
        bot "TestBot"
        on message {
            if message.text == "ping" {
                send "pong"
            }
        }
        '''
        prog = self._parse(code)
        on_msg = prog.declarations[1]
        self.assertIsInstance(on_msg, OnMessageDecl)
        self.assertIsInstance(on_msg.body.statements[0], IfStmt)

    def test_parse_member_access(self):
        code = '''
        bot "TestBot"
        command "/info" {
            name = user.name
            send user.username
        }
        '''
        prog = self._parse(code)
        cmd = prog.declarations[1]
        assign_stmt = cmd.body.statements[0]
        self.assertIsInstance(assign_stmt, VariableAssignStmt)
        self.assertIsInstance(assign_stmt.value, MemberAccessExpr)
        self.assertEqual(assign_stmt.value.member, "name")


if __name__ == "__main__":
    unittest.main()
