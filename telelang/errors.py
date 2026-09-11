"""Модуль ошибок TeleLang с информативным форматированием."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SourceSpan:
    """Указатель на фрагмент исходного кода."""
    line: int        # 1-indexed
    column: int      # 1-indexed
    length: int = 1
    file_path: Optional[str] = None

    def __str__(self) -> str:
        loc = f"строка {self.line}, колонка {self.column}"
        if self.file_path:
            return f"{self.file_path}:{self.line}:{self.column}"
        return loc


class TeleLangError(Exception):
    """Базовое исключение для ошибок TeleLang."""

    def __init__(
        self,
        message: str,
        span: Optional[SourceSpan] = None,
        source_code: Optional[str] = None,
        hint: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.span = span
        self.source_code = source_code
        self.hint = hint

    def format_report(self) -> str:
        """Форматирует человекочитаемый отчёт об ошибке."""
        lines = []

        if self.span:
            file_info = f" в файле '{self.span.file_path}'" if self.span.file_path else ""
            lines.append(f"Ошибка в строке {self.span.line}{file_info}:")
            lines.append("")

            if self.source_code:
                code_lines = self.source_code.splitlines()
                if 1 <= self.span.line <= len(code_lines):
                    src_line = code_lines[self.span.line - 1]
                    lines.append(f"    {src_line}")
                    # Рисуем стрелочку под ошибкой
                    pointer_indent = " " * (4 + max(0, self.span.column - 1))
                    pointer = "^" * max(1, self.span.length)
                    lines.append(f"{pointer_indent}{pointer}")
                    lines.append("")
        else:
            lines.append("Ошибка:")
            lines.append("")

        lines.append(self.message)

        if self.hint:
            lines.append("")
            lines.append(f"Подсказка: {self.hint}")

        return "\n".join(lines)

    def __str__(self) -> str:
        return self.format_report()


class TeleLangSyntaxError(TeleLangError):
    """Синтаксическая ошибка на этапе лексического анализа или парсинга."""
    pass


class TeleLangSemanticError(TeleLangError):
    """Семантическая ошибка (несовместимость типов, дублирование, отсутствие настроек)."""
    pass


class TeleLangRuntimeError(TeleLangError):
    """Ошибка времени выполнения."""
    pass


class TeleLangConfigError(TeleLangError):
    """Ошибка конфигурации или отсутствия секретов (.env / --token)."""
    pass
