"""Лексический анализатор TeleLang (Этап 3)."""

from __future__ import annotations
from typing import Optional
from telelang.errors import SourceSpan, TeleLangSyntaxError
from telelang.lexer.tokens import KEYWORDS, Token, TokenType


class Lexer:
    """Лексер, преобразующий исходный код TeleLang в последовательность токенов."""

    def __init__(self, source_code: str, file_path: Optional[str] = None):
        self.source = source_code
        self.file_path = file_path
        self.pos = 0
        self.line = 1
        self.col = 1
        self.length = len(source_code)

    def _current_char(self) -> Optional[str]:
        if self.pos >= self.length:
            return None
        return self.source[self.pos]

    def _peek_char(self, offset: int = 1) -> Optional[str]:
        p = self.pos + offset
        if p >= self.length:
            return None
        return self.source[p]

    def _advance(self) -> Optional[str]:
        char = self._current_char()
        self.pos += 1
        if char == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return char

    def tokenize(self) -> list[Token]:
        """Токенизирует весь исходный код."""
        tokens: list[Token] = []

        while self.pos < self.length:
            char = self._current_char()

            # Пропуск пробелов
            if char in (" ", "\t", "\r", "\n"):
                self._advance()
                continue

            # Пропуск комментариев (# ...)
            if char == "#":
                while self._current_char() is not None and self._current_char() != "\n":
                    self._advance()
                continue

            start_line = self.line
            start_col = self.col

            # Строковые литералы: "..."
            if char == '"':
                tokens.append(self._read_string(start_line, start_col))
                continue

            # Числа
            if char.isdigit():
                tokens.append(self._read_number(start_line, start_col))
                continue

            # Идентификаторы и ключевые слова
            if char.isalpha() or char == "_":
                tokens.append(self._read_identifier(start_line, start_col))
                continue

            # Двухсимвольные и односимвольные операторы
            if char == "+":
                self._advance()
                if self._current_char() == "=":
                    self._advance()
                    tokens.append(Token(TokenType.PLUS_EQUALS, "+=", SourceSpan(start_line, start_col, 2, self.file_path)))
                else:
                    tokens.append(Token(TokenType.PLUS, "+", SourceSpan(start_line, start_col, 1, self.file_path)))
                continue

            if char == "-":
                self._advance()
                if self._current_char() == ">":
                    self._advance()
                    tokens.append(Token(TokenType.ARROW, "->", SourceSpan(start_line, start_col, 2, self.file_path)))
                elif self._current_char() == "=":
                    self._advance()
                    tokens.append(Token(TokenType.MINUS_EQUALS, "-=", SourceSpan(start_line, start_col, 2, self.file_path)))
                else:
                    tokens.append(Token(TokenType.MINUS, "-", SourceSpan(start_line, start_col, 1, self.file_path)))
                continue

            if char == "=":
                self._advance()
                if self._current_char() == "=":
                    self._advance()
                    tokens.append(Token(TokenType.EQEQ, "==", SourceSpan(start_line, start_col, 2, self.file_path)))
                else:
                    tokens.append(Token(TokenType.EQUALS, "=", SourceSpan(start_line, start_col, 1, self.file_path)))
                continue

            if char == "!":
                self._advance()
                if self._current_char() == "=":
                    self._advance()
                    tokens.append(Token(TokenType.NOT_EQ, "!=", SourceSpan(start_line, start_col, 2, self.file_path)))
                else:
                    span = SourceSpan(start_line, start_col, 1, self.file_path)
                    raise TeleLangSyntaxError(
                        "Неожиданный символ '!'. Возможно, имелось в виду '!='?",
                        span=span,
                        source_code=self.source,
                    )
                continue

            if char == "<":
                self._advance()
                if self._current_char() == "=":
                    self._advance()
                    tokens.append(Token(TokenType.LTE, "<=", SourceSpan(start_line, start_col, 2, self.file_path)))
                else:
                    tokens.append(Token(TokenType.LT, "<", SourceSpan(start_line, start_col, 1, self.file_path)))
                continue

            if char == ">":
                self._advance()
                if self._current_char() == "=":
                    self._advance()
                    tokens.append(Token(TokenType.GTE, ">=", SourceSpan(start_line, start_col, 2, self.file_path)))
                else:
                    tokens.append(Token(TokenType.GT, ">", SourceSpan(start_line, start_col, 1, self.file_path)))
                continue

            if char == "*":
                self._advance()
                tokens.append(Token(TokenType.STAR, "*", SourceSpan(start_line, start_col, 1, self.file_path)))
                continue

            if char == "/":
                self._advance()
                tokens.append(Token(TokenType.SLASH, "/", SourceSpan(start_line, start_col, 1, self.file_path)))
                continue

            if char == ":":
                self._advance()
                tokens.append(Token(TokenType.COLON, ":", SourceSpan(start_line, start_col, 1, self.file_path)))
                continue

            if char == "{":
                self._advance()
                tokens.append(Token(TokenType.LBRACE, "{", SourceSpan(start_line, start_col, 1, self.file_path)))
                continue

            if char == "}":
                self._advance()
                tokens.append(Token(TokenType.RBRACE, "}", SourceSpan(start_line, start_col, 1, self.file_path)))
                continue

            if char == "(":
                self._advance()
                tokens.append(Token(TokenType.LPAREN, "(", SourceSpan(start_line, start_col, 1, self.file_path)))
                continue

            if char == ")":
                self._advance()
                tokens.append(Token(TokenType.RPAREN, ")", SourceSpan(start_line, start_col, 1, self.file_path)))
                continue

            if char == "[":
                self._advance()
                tokens.append(Token(TokenType.LBRACKET, "[", SourceSpan(start_line, start_col, 1, self.file_path)))
                continue

            if char == "]":
                self._advance()
                tokens.append(Token(TokenType.RBRACKET, "]", SourceSpan(start_line, start_col, 1, self.file_path)))
                continue

            if char == ".":
                self._advance()
                tokens.append(Token(TokenType.DOT, ".", SourceSpan(start_line, start_col, 1, self.file_path)))
                continue

            if char == ",":
                self._advance()
                tokens.append(Token(TokenType.COMMA, ",", SourceSpan(start_line, start_col, 1, self.file_path)))
                continue

            # Неопознанный символ
            unknown_char = self._advance()
            span = SourceSpan(start_line, start_col, 1, self.file_path)
            raise TeleLangSyntaxError(
                f"Неожиданный символ: {unknown_char!r}",
                span=span,
                source_code=self.source,
                hint="Проверь синтаксис исходного файла на наличие опечаток или недопустимых символов.",
            )

        # Конец файла
        eof_span = SourceSpan(self.line, self.col, 1, self.file_path)
        tokens.append(Token(TokenType.EOF, "", eof_span))
        return tokens

    def _read_string(self, start_line: int, start_col: int) -> Token:
        """Считывает строковый литерал в двойных кавычках."""
        self._advance()
        chars: list[str] = []

        while True:
            char = self._current_char()
            if char is None or char == "\n":
                span = SourceSpan(start_line, start_col, max(1, self.col - start_col), self.file_path)
                raise TeleLangSyntaxError(
                    "Незакрытая строковая константа.",
                    span=span,
                    source_code=self.source,
                    hint='Добавь закрывающую кавычку `"` в конце строки.',
                )

            if char == '"':
                self._advance()
                break

            if char == "\\":
                self._advance()
                esc = self._current_char()
                if esc == "n":
                    chars.append("\n")
                elif esc == "t":
                    chars.append("\t")
                elif esc == '"':
                    chars.append('"')
                elif esc == "\\":
                    chars.append("\\")
                elif esc is None:
                    span = SourceSpan(start_line, start_col, max(1, self.col - start_col), self.file_path)
                    raise TeleLangSyntaxError(
                        "Незавершённая escape-последовательность в строке.",
                        span=span,
                        source_code=self.source,
                    )
                else:
                    chars.append(esc)
                self._advance()
            else:
                chars.append(char)
                self._advance()

        val = "".join(chars)
        length = self.pos - (start_col - 1)
        span = SourceSpan(start_line, start_col, max(1, length), self.file_path)
        return Token(TokenType.STRING, val, span)

    def _read_number(self, start_line: int, start_col: int) -> Token:
        """Считывает число (целое или с плавающей точкой)."""
        digits: list[str] = []
        has_dot = False

        while self._current_char() is not None:
            char = self._current_char()
            if char.isdigit():
                digits.append(char)
                self._advance()
            elif char == "." and not has_dot and self._peek_char() and self._peek_char().isdigit():
                has_dot = True
                digits.append(char)
                self._advance()
            else:
                break

        num_str = "".join(digits)
        val = float(num_str) if has_dot else int(num_str)
        span = SourceSpan(start_line, start_col, len(num_str), self.file_path)
        return Token(TokenType.NUMBER, val, span)

    def _read_identifier(self, start_line: int, start_col: int) -> Token:
        """Считывает идентификатор или ключевое слово."""
        chars: list[str] = []

        while self._current_char() is not None:
            char = self._current_char()
            if char.isalnum() or char == "_":
                chars.append(char)
                self._advance()
            else:
                break

        ident = "".join(chars)
        token_type = KEYWORDS.get(ident, TokenType.IDENTIFIER)
        span = SourceSpan(start_line, start_col, len(ident), self.file_path)
        return Token(token_type, ident, span)
