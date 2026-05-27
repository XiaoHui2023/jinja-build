from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from rich.console import Group
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

_CONTEXT_MARGIN = 2


def error_title(exc_type: str, headline: str) -> Text:
    """错误卡片顶部：类型 + 摘要。"""
    title = Text()
    title.append(exc_type, style="error.title")
    title.append(" — ", style="error.dim")
    title.append(headline, style="error.message")
    return title


def meta_grid(rows: Sequence[tuple[str, str, str]]) -> Table:
    """两列元信息表：标签 | 值（值带独立 style）。"""
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="error.label", no_wrap=True)
    grid.add_column()
    for label, value, value_style in rows:
        grid.add_row(label, Text(value, style=value_style))
    return grid


def field_errors_table(
    columns: Sequence[tuple[str, str]],
    rows: Sequence[tuple[str, str, str, str]],
) -> Table:
    """字段级问题表。"""
    table = Table(show_header=True, header_style="error.label", box=None, padding=(0, 1))
    for title, col_style in columns:
        table.add_column(title, style=col_style, no_wrap=title in ("字段", "类型"))
    for row in rows:
        table.add_row(*row)
    return table


def file_context_group(path: Path, lineno: int) -> Group | None:
    """带行号的文件上下文，与元信息分块展示。"""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    if not lines or lineno < 1:
        return None

    parts: list[Text | Rule] = [Text(str(path), style="error.path")]
    start = max(1, lineno - _CONTEXT_MARGIN)
    end = min(len(lines), lineno + _CONTEXT_MARGIN)
    for num in range(start, end + 1):
        style = "error.line_highlight" if num == lineno else "error.line_body"
        parts.append(
            Text.assemble(
                (f"{num:>4} ", "error.line_no"),
                (lines[num - 1].rstrip("\n"), style),
            )
        )
    return Group(*parts)


def hints_block(hints: Sequence[str]) -> Group | None:
    if not hints:
        return None
    return Group(*[Text(hint, style="error.dim") for hint in hints])


def print_error_card(
    console: object,
    *,
    title: Text,
    body_parts: Sequence[object],
    context: Group | None = None,
) -> None:
    """输出单张聚合错误卡片。"""
    sections: list[object] = [title, *body_parts]
    if context is not None:
        sections.extend([Rule(style="error.dim"), context])
    card = Panel(
        Group(*sections),
        border_style="error.title",
        padding=(1, 2),
    )
    console.print(card)  # type: ignore[attr-defined]


__all__ = [
    "error_title",
    "meta_grid",
    "field_errors_table",
    "file_context_group",
    "hints_block",
    "print_error_card",
]
