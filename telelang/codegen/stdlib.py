"""Lower standard TeleLang expressions to standalone Python."""

from collections.abc import Callable

from telelang.parser.ast_nodes import Expr, FunctionCallExpr, MemberAccessExpr, StringLiteral

STD_IMPORTS = (
    "import builtins as _tl_builtin",
    "from random import randint as _tl_randint",
    "from time import time as _tl_clock",
)


def emit_std(expr: Expr, emit: Callable[[Expr], str]) -> str | None:
    if isinstance(expr, FunctionCallExpr) and expr.func_name == "random":
        return f"_tl_randint({emit(expr.args[0])}, {emit(expr.args[1])})"
    if isinstance(expr, MemberAccessExpr):
        if expr.is_time_now:
            return "_tl_builtin.int(_tl_clock())"
        if expr.member in ("length", "lower", "upper"):
            method = "__len__" if expr.member == "length" else expr.member
            return f"_tl_builtin.str.{method}({emit(expr.target)})"
    return None


def emit_send_text(expr: Expr, emit: Callable[[Expr], str]) -> str:
    value = emit(expr)
    return value if isinstance(expr, StringLiteral) else f"_tl_builtin.str({value})"
