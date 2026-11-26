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
    """Разрешает зависимости и импорты файлов .tl и директорий с обнаружением циклов."""

    def __init__(self):
        self.loaded_files: dict[Path, Program] = {}
        self.file_programs: dict[Path, Program] = {}
        self.resolved_files: list[Path] = []
        self.call_stack: list[Path] = []
        self.imported_dirs: set[Path] = set()

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

        if file_path in self.loaded_files:
            return self.loaded_files[file_path]

        self.call_stack.append(file_path)
        source_code = file_path.read_text(encoding="utf-8")

        # Парсим файл
        lexer = Lexer(source_code=source_code, file_path=str(file_path))
        tokens = lexer.tokenize()
        parser = Parser(tokens=tokens, source_code=source_code, file_path=str(file_path))
        program = parser.parse()

        self.file_programs[file_path] = program
        if file_path not in self.resolved_files:
            self.resolved_files.append(file_path)

        # Разрешаем импорты внутри этого файла
        merged_declarations: list[Declaration] = []

        for decl in program.declarations:
            if isinstance(decl, ImportDecl):
                # Разрешаем путь относительно текущего файла
                raw_target = file_path.parent / decl.path
                imported_path = raw_target.resolve()

                # Автоматическое дополнение расширения .tl если не указано
                if not imported_path.exists() and imported_path.with_suffix(".tl").exists():
                    imported_path = imported_path.with_suffix(".tl")

                if not imported_path.exists():
                    raise TeleLangError(
                        f"Импортируемый путь '{decl.path}' не найден (искался в '{imported_path}').",
                        hint="Проверьте правильность пути к файлу или папке.",
                    )

                # 1. Импорт директории (например, import "commands/")
                if imported_path.is_dir():
                    self.imported_dirs.add(imported_path)
                    child_tl_files = sorted(list(imported_path.glob("*.tl")))
                    for child_file in child_tl_files:
                        child_prog = self._load_file(child_file)
                        for imp_decl in child_prog.declarations:
                            if isinstance(imp_decl, ImportDecl):
                                continue
                            if decl.alias and isinstance(imp_decl, FunctionDecl):
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
                    # 2. Импорт отдельного файла
                    imported_prog = self._load_file(imported_path)
                    for imp_decl in imported_prog.declarations:
                        if isinstance(imp_decl, ImportDecl):
                            continue
                        if decl.alias and isinstance(imp_decl, FunctionDecl):
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
        self.loaded_files[file_path] = merged_program
        return merged_program


class ProjectLoader:
    """Утилита для обнаружения точки входа и разрешения путей проекта."""

    ENTRYPOINT_NAMES = ["main.tl", "bot.tl", "app.tl"]

    @classmethod
    def resolve_target(cls, target_path: str | Path) -> tuple[Path, Path, str]:
        """
        Разрешает путь к цели (файл или директория).
        Возвращает кортеж: (entrypoint_file, project_root_dir, project_name)
        """
        raw_path = Path(target_path).resolve()
        if raw_path.is_file():
            entrypoint = raw_path
            project_dir = raw_path.parent
            project_name = project_dir.name if project_dir.name not in (".", "", "/") else raw_path.stem
            return entrypoint, project_dir, project_name
        elif raw_path.is_dir():
            project_dir = raw_path
            project_name = project_dir.name if project_dir.name not in (".", "") else project_dir.resolve().name
            for name in cls.ENTRYPOINT_NAMES:
                candidate = project_dir / name
                if candidate.is_file():
                    return candidate, project_dir, project_name
            # Поиск любого .tl файла в корне с bot или userbot
            tl_files = sorted(list(project_dir.glob("*.tl")))
            for candidate in tl_files:
                try:
                    content = candidate.read_text(encoding="utf-8", errors="ignore")
                    if "bot " in content or "userbot " in content:
                        return candidate, project_dir, project_name
                except Exception:
                    pass
            if tl_files:
                return tl_files[0], project_dir, project_name
            raise TeleLangError(
                f"В директории '{project_dir}' не найден главный файл (main.tl, bot.tl или app.tl).",
                hint="Создайте файл main.tl в корне проекта или укажите путь к файлу напрямую.",
            )
        else:
            raise TeleLangError(
                f"Путь '{target_path}' не найден.",
                hint="Проверьте правильность пути к файлу или папке проекта.",
            )


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
    def load_project(cls, target_path: str | Path) -> tuple[Program, ModuleResolver, Path, Path, str]:
        """
        Загружает проект из файла или директории.
        Возвращает: (merged_program, resolver, entrypoint_path, project_dir, project_name)
        """
        entrypoint, project_dir, project_name = ProjectLoader.resolve_target(target_path)
        resolver = ModuleResolver()
        program = resolver.resolve(entrypoint)
        analyzer = SemanticAnalyzer(source_code=entrypoint.read_text(encoding="utf-8"), file_path=str(entrypoint))
        analyzer.analyze(program, is_entrypoint=True)
        return program, resolver, entrypoint, project_dir, project_name

    @classmethod
    def compile_file(cls, file_path: str | Path) -> tuple[Program, str]:
        """Читает файл .tl или директорию, разрешает импорты и компилирует его."""
        path = Path(file_path).resolve()
        if path.is_dir():
            path, _, _ = ProjectLoader.resolve_target(path)
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
