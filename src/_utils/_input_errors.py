from __future__ import annotations

import inspect
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ._jinja_rich import jinja_error_console

_INPUT_VALUE_MAX = 120


@dataclass(frozen=True)
class InputFieldError:
    """单条字段级校验问题。"""

    loc: str
    kind: str
    message: str
    input_value: str


@dataclass(frozen=True)
class InputLoadErrorReport:
    """整理后的输入加载错误，供终端展示。"""

    exc_type: str
    headline: str
    stage: str
    input_path: Path | None
    models_path: Path
    models_type_name: str | None
    field_errors: tuple[InputFieldError, ...]
    hints: tuple[str, ...]
    context_path: Path | None
    context_lineno: int | None


def build_input_load_error_report(
    exc: BaseException,
    *,
    input_path: Path | None,
    models_path: Path,
    models_type: type | None = None,
    stage: str,
) -> InputLoadErrorReport:
    """从异常收集输入路径、模型类型与字段级详情。"""
    if isinstance(exc, ValidationError):
        return _report_from_validation_error(
            exc,
            input_path=input_path,
            models_path=models_path,
            models_type=models_type,
            stage=stage,
        )
    if isinstance(exc, TypeError):
        return _report_from_type_error(
            exc,
            input_path=input_path,
            models_path=models_path,
            models_type=models_type,
            stage=stage,
        )
    return _report_generic(
        exc,
        input_path=input_path,
        models_path=models_path,
        models_type=models_type,
        stage=stage,
    )


def print_input_model_error(
    exc: BaseException,
    *,
    input_path: Path | None,
    models_path: Path,
    models_type: type | None = None,
    stage: str,
) -> None:
    """用 Rich 打印输入配置载入或填入 models 时的错误。"""
    report = build_input_load_error_report(
        exc,
        input_path=input_path,
        models_path=models_path,
        models_type=models_type,
        stage=stage,
    )
    console = jinja_error_console()

    title = Text()
    title.append(report.exc_type, style="error.title")
    title.append(" — ", style="error.dim")
    title.append(report.headline, style="error.message")
    console.print(Panel(title, border_style="error.title", padding=(0, 1)))

    console.print(
        Text.assemble(
            ("阶段", "error.label"),
            ("  ", ""),
            (_stage_description(report.stage), "error.dim"),
        )
    )
    _print_meta(console, report)

    if report.context_path is not None and report.context_lineno:
        _print_file_context(console, report.context_path, report.context_lineno)

    if report.field_errors:
        table = Table(show_header=True, header_style="error.label", box=None, padding=(0, 1))
        table.add_column("字段", style="error.path", no_wrap=True)
        table.add_column("问题", style="error.message")
        table.add_column("类型", style="error.dim", no_wrap=True)
        table.add_column("收到", style="error.line_body")
        for item in report.field_errors:
            table.add_row(item.loc, item.message, item.kind, item.input_value)
        console.print(table)

    for hint in report.hints:
        console.print(Text(hint, style="error.dim"))


def _print_meta(console: object, report: InputLoadErrorReport) -> None:
    if report.input_path is not None:
        console.print(  # type: ignore[attr-defined]
            Text.assemble(
                ("输入配置", "error.label"),
                ("  ", ""),
                (str(report.input_path), "error.path"),
            )
        )
    else:
        console.print(  # type: ignore[attr-defined]
            Text.assemble(
                ("输入配置", "error.label"),
                ("  ", ""),
                ("（未指定，使用空对象）", "error.dim"),
            )
        )

    if report.models_type_name:
        console.print(  # type: ignore[attr-defined]
            Text.assemble(
                ("数据类型", "error.label"),
                ("  ", ""),
                (report.models_type_name, "error.path"),
            )
        )
    console.print(  # type: ignore[attr-defined]
        Text.assemble(
            ("models 文件", "error.label"),
            ("  ", ""),
            (str(report.models_path), "error.path"),
        )
    )


def _print_file_context(console: object, path: Path, lineno: int) -> None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    if not lines or lineno < 1:
        return

    console.print(Text(str(path), style="error.path"))  # type: ignore[attr-defined]
    start = max(1, lineno - 2)
    end = min(len(lines), lineno + 2)
    for num in range(start, end + 1):
        style = "error.line_highlight" if num == lineno else "error.line_body"
        console.print(  # type: ignore[attr-defined]
            Text.assemble(
                (f"{num:>4} ", "error.line_no"),
                (lines[num - 1].rstrip("\n"), style),
            )
        )


def _report_from_validation_error(
    exc: ValidationError,
    *,
    input_path: Path | None,
    models_path: Path,
    models_type: type | None,
    stage: str,
) -> InputLoadErrorReport:
    model_name = models_type.__name__ if models_type is not None else "Model"
    count = len(exc.errors())
    headline = f"{count} 处字段不符合 {model_name}"
    field_errors = tuple(
        InputFieldError(
            loc=_format_loc(tuple(item.get("loc", ()))),
            kind=str(item.get("type", "")),
            message=str(item.get("msg", "")),
            input_value=_format_input_value(item.get("input")),
        )
        for item in exc.errors()
    )
    hints = _model_field_hints(models_type)
    return InputLoadErrorReport(
        exc_type=type(exc).__name__,
        headline=headline,
        stage=stage,
        input_path=input_path,
        models_path=models_path.resolve(),
        models_type_name=model_name,
        field_errors=field_errors,
        hints=hints,
        context_path=input_path.resolve() if input_path else None,
        context_lineno=None,
    )


def _report_from_type_error(
    exc: TypeError,
    *,
    input_path: Path | None,
    models_path: Path,
    models_type: type | None,
    stage: str,
) -> InputLoadErrorReport:
    message = str(exc).strip() or type(exc).__name__
    hints = list(_model_field_hints(models_type))
    if stage == "config":
        hints.insert(0, "配置文件解析结果必须是键值映射（dict），不能是列表或其它顶层类型。")
    return InputLoadErrorReport(
        exc_type=type(exc).__name__,
        headline=message,
        stage=stage,
        input_path=input_path,
        models_path=models_path.resolve(),
        models_type_name=models_type.__name__ if models_type is not None else None,
        field_errors=(),
        hints=tuple(hints),
        context_path=input_path.resolve() if input_path else None,
        context_lineno=None,
    )


def _report_generic(
    exc: BaseException,
    *,
    input_path: Path | None,
    models_path: Path,
    models_type: type | None,
    stage: str,
) -> InputLoadErrorReport:
    message = str(exc).strip() or type(exc).__name__
    context_path = input_path.resolve() if input_path else None
    context_lineno = _exception_lineno(exc)
    hints = _model_field_hints(models_type) if stage == "model" else ()
    return InputLoadErrorReport(
        exc_type=type(exc).__name__,
        headline=message,
        stage=stage,
        input_path=input_path,
        models_path=models_path.resolve(),
        models_type_name=models_type.__name__ if models_type is not None else None,
        field_errors=(),
        hints=hints,
        context_path=context_path,
        context_lineno=context_lineno,
    )


def _stage_description(stage: str) -> str:
    if stage == "config":
        return "读取配置文件"
    if stage == "model":
        return "填入数据模型"
    return stage


def _format_loc(loc: Sequence[Any]) -> str:
    if not loc:
        return "(root)"
    out = str(loc[0])
    for item in loc[1:]:
        if isinstance(item, int):
            out += f"[{item}]"
        else:
            out += f".{item}"
    return out


def _format_input_value(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, (dict, list, tuple)):
        try:
            text = json.dumps(value, ensure_ascii=False, default=str)
        except TypeError:
            text = repr(value)
    else:
        text = repr(value)
    if len(text) > _INPUT_VALUE_MAX:
        return text[: _INPUT_VALUE_MAX - 3] + "..."
    return text


def _model_field_hints(models_type: type | None) -> tuple[str, ...]:
    if models_type is None:
        return ()
    hints: list[str] = []
    if issubclass(models_type, BaseModel):
        names = list(models_type.model_fields.keys())
        if names:
            hints.append("模型字段: " + ", ".join(names))
        return tuple(hints)

    try:
        signature = inspect.signature(models_type.__init__)
    except (TypeError, ValueError):
        return tuple(hints)

    params = [
        name
        for name, param in signature.parameters.items()
        if name != "self" and param.kind in (param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY)
    ]
    if params:
        hints.append("__init__ 参数: " + ", ".join(params))
    return tuple(hints)


def _exception_lineno(exc: BaseException) -> int | None:
    lineno = getattr(exc, "lineno", None)
    if isinstance(lineno, int) and lineno > 0:
        return lineno
    mark = getattr(exc, "problem_mark", None)
    if mark is not None:
        line = getattr(mark, "line", None)
        if isinstance(line, int):
            return line + 1
    return None


__all__ = [
    "InputFieldError",
    "InputLoadErrorReport",
    "build_input_load_error_report",
    "print_input_model_error",
]
