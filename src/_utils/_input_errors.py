from __future__ import annotations

import inspect
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rich.table import Table

from pydantic import BaseModel, ValidationError

from ._error_card import (
    error_title,
    field_errors_table,
    file_context_group,
    hints_block,
    meta_grid,
    print_error_card,
)
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
    body: list[object] = [_meta_rows(report)]
    if report.field_errors:
        body.append(
            field_errors_table(
                (
                    ("字段", "error.path"),
                    ("问题", "error.message"),
                    ("类型", "error.dim"),
                    ("收到", "error.line_body"),
                ),
                tuple(
                    (item.loc, item.message, item.kind, item.input_value)
                    for item in report.field_errors
                ),
            )
        )
    hints = hints_block(report.hints)
    if hints is not None:
        body.append(hints)

    context = None
    if report.context_path is not None and report.context_lineno:
        context = file_context_group(report.context_path, report.context_lineno)

    print_error_card(
        console,
        title=error_title(report.exc_type, report.headline),
        body_parts=body,
        context=context,
    )


def _meta_rows(report: InputLoadErrorReport) -> Table:
    rows: list[tuple[str, str, str]] = [
        ("阶段", _stage_description(report.stage), "error.dim"),
    ]
    if report.input_path is not None:
        rows.append(("输入配置", str(report.input_path), "error.path"))
    else:
        rows.append(("输入配置", "（未指定，使用空对象）", "error.dim"))
    if report.models_type_name:
        rows.append(("数据类型", report.models_type_name, "error.path"))
    rows.append(("models 文件", str(report.models_path), "error.path"))
    return meta_grid(rows)


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
