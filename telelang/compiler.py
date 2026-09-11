"""Главный конвейер компиляции TeleLang с поддержкой модулей и циклических импортов."""

from __future__ import annotations
from pathlib import Path
from typing import Optional
from telelang.codegen.python_emitter import PythonEmitter
from telelang.errors import SourceSpan, TeleLangError, TeleLangSemanticError
from telelang.lexer.lexer import Lexer
from telelang.parser.ast_nodes import (
    Declaration,
    FunctionDecl,
    ImportDecl,
    Program,
)
from telelang.parser.parser import Parser
from telelang.semantic.analyzer import SemanticAnalyzer


class ModuleResolver:
    """Разрешает зависимости и импорты файлов .tl с обнаружением циклов."""

    def __init__(self):
        self.loaded_files: dict[Path, Program] = {}
        self.call_stack: list[Path] = []

    def resolve(self, entrypoint_path: Path) -> Program:
        """Рекурсивно разрешает все импорты начиная с точки входа."""
        entry = entrypoint_path.resolve()
        return self._load_file(entry)

    def _load_file(self, file_path: Path) -> Program:
        if file_path in self.call_stack:
            chain = " -> ".join([p.name for p in self.call_stack]) + f" -> {file_path.name}"
            raise TeleLangSemanticError(
                f"Обнаружен циклический импорт:\n  {chain}",
                hint="Устрани циклическую зависимость между файлами.",
            )

        if not file_path.exists():
            raise TeleLangError(
                f"Импортируемый файл '{file_path}' не найден.",
                hint="Проверь путь к файлу и его существование.",
            )

        self.call_stack.append(file_path)
        source_code = file_path.read_text(encoding="utf-8")

        # Парсим файл
        lexer = Lexer(source_code=source_code, file_path=str(file_path))
        tokens = lexer.tokenize()
        parser = Parser(tokens=tokens, source_code=source_code, file_path=str(file_path))
        program = parser.parse()

        # Разрешаем импорты внутри этого файла
        merged_declarations: list[Declaration] = []

        for decl in program.declarations:
            if isinstance(decl, ImportDecl):
                # Разрешаем путь относительно текущего файла
                imported_path = (file_path.parent / decl.path).resolve()
                imported_prog = self._load_file(imported_path)

                # Встраиваем объявления импортированного модуля
                for imp_decl in imported_prog.declarations:
                    if isinstance(imp_decl, ImportDecl):
                        continue
                    if decl.alias and isinstance(imp_decl, FunctionDecl):
                        # Префиксируем имя функции псевдонимом (shop.open)
                        aliased_fn = FunctionDecl(
                            name=f"{decl.alias}_{imp_decl.name}",
                            body=imp_decl.body,
                            params=imp_decl.params,
                            span=imp_decl.span,
                        )
                        merged_declarations.append(aliased_fn)
                    else:
                        merged_declarations.append(imp_decl)
            else:
                merged_declarations.append(decl)

        self.call_stack.pop()
        merged_program = Program(declarations=merged_declarations, span=program.span)
        return merged_program


class TeleCompiler:
    """Оркестратор полного конвейера компиляции TeleLang:

    .tl -> Lexer -> Parser -> ModuleResolver -> SemanticAnalyzer -> PythonEmitter -> Python code.
    """

    @classmethod
    def compile_source(cls, source_code: str, file_path: Optional[str] = None) -> tuple[Program, str]:
        """Компилирует исходный код в AST и сгенерированный Python-код."""
        lexer = Lexer(source_code=source_code, file_path=file_path)
        tokens = lexer.tokenize()

        parser = Parser(tokens=tokens, source_code=source_code, file_path=file_path)
        program = parser.parse()

        analyzer = SemanticAnalyzer(source_code=source_code, file_path=file_path)
        analyzer.analyze(program, is_entrypoint=True)

        from telelang.parser.ast_nodes import UserbotDecl
        is_userbot = any(isinstance(d, UserbotDecl) for d in program.declarations)
        if is_userbot:
            from telelang.telegram.userbot_backend.emitter import TelethonEmitter
            emitter = TelethonEmitter(program)
        else:
            emitter = PythonEmitter(program)

        python_code = emitter.emit()
        return program, python_code

    @classmethod
    def compile_file(cls, file_path: str | Path) -> tuple[Program, str]:
        """Читает файл .tl, разрешает импорты и компилирует его."""
        path = Path(file_path).resolve()
        resolver = ModuleResolver()
        program = resolver.resolve(path)

        analyzer = SemanticAnalyzer(source_code=path.read_text(encoding="utf-8"), file_path=str(path))
        analyzer.analyze(program, is_entrypoint=True)

        from telelang.parser.ast_nodes import UserbotDecl
        is_userbot = any(isinstance(d, UserbotDecl) for d in program.declarations)
        if is_userbot:
            from telelang.telegram.userbot_backend.emitter import TelethonEmitter
            emitter = TelethonEmitter(program)
        else:
            emitter = PythonEmitter(program)

        python_code = emitter.emit()
        return program, python_code
