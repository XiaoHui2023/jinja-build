from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import TracebackType

from jinja2.exceptions import TemplateError, TemplateNotFound, TemplateSyntaxError
from rich.panel import Panel
from rich.text import Text

from ._jinja_rich import jinja_error_console

_TEMPLATE_SUFFIXES = (".j2", ".jinja", ".jinja2", ".html.j2", ".xml.j2", ".txt.j2")
_CONTEXT_LINES = 2


@dataclass(frozen=True)
class TemplateErrorSite:
    """模板栈中的一处位置。"""

    path: Path
    lineno: int
    location: str
    line_text: str


@dataclass(frozen=True)
class TemplateErrorReport:
    """整理后的模板错误，供终端展示。"""

    exc_type: str
    message: str
    entry_path: Path | None
    sites: tuple[TemplateErrorSite, ...]
    extra: tuple[str, ...]


def build_template_error_report(
    exc: BaseException,
    entry_path: Path | None = None,
) -> TemplateErrorReport:
    """从异常收集模板路径、行号与上下文，不依赖完整 Python 栈。"""
    message = _exception_message(exc)
    extra: list[str] = list(_cause_messages(exc))
    sites: list[TemplateErrorSite] = []

    if isinstance(exc, TemplateSyntaxError):
        sites.extend(_sites_from_syntax_error(exc))
    elif isinstance(exc, TemplateNotFound):
        extra.insert(0, f"模板名: {exc.name}")
        if exc.templates:
            extra.insert(1, "已尝试: " + ", ".join(str(name) for name in exc.templates))
    else:
        sites.extend(_sites_from_traceback(exc))

    if not sites and entry_path is not None:
        sites.append(
            TemplateErrorSite(
                path=entry_path.resolve(),
                lineno=1,
                location="",
                line_text="",
            )
        )

    return TemplateErrorReport(
        exc_type=type(exc).__name__,
        message=message,
        entry_path=entry_path.resolve() if entry_path else None,
        sites=tuple(sites),
        extra=tuple(extra),
    )


def print_template_error(
    exc: BaseException,
    entry_path: Path | None = None,
) -> None:
    """用 Rich 打印模板错误（仅含模板相关位置）。"""
    report = build_template_error_report(exc, entry_path=entry_path)
    console = jinja_error_console()

    title = Text()
    title.append(report.exc_type, style="error.title")
    title.append(" — ", style="error.dim")
    title.append(report.message, style="error.message")

    console.print(Panel(title, border_style="error.title", padding=(0, 1)))

    if report.entry_path is not None:
        console.print(
            Text.assemble(
                ("入口模板", "error.label"),
                ("  ", ""),
                (str(report.entry_path), "error.path"),
            )
        )

    for index, site in enumerate(report.sites):
        if index > 0:
            console.print(Text("↑ 由下列位置调用", style="error.dim"))
        _print_site(console, site)

    for line in report.extra:
        console.print(Text(line, style="error.dim"))


def _print_site(console: object, site: TemplateErrorSite) -> None:
    header = Text()
    header.append(str(site.path), style="error.path")
    if site.location:
        header.append(f"  ({site.location})", style="error.dim")
    console.print(header)  # type: ignore[attr-defined]

    if site.lineno < 1:
        return

    rows = _read_context_lines(site.path, site.lineno)
    if not rows and site.line_text:
        console.print(
            Text.assemble(
                (f"{site.lineno:>4} ", "error.line_no"),
                (site.line_text.rstrip(), "error.line_highlight"),
            )
        )  # type: ignore[attr-defined]
        return

    for num, text, is_error in rows:
        style = "error.line_highlight" if is_error else "error.line_body"
        console.print(
            Text.assemble(
                (f"{num:>4} ", "error.line_no"),
                (text.rstrip("\n"), style),
            )
        )  # type: ignore[attr-defined]


def _read_context_lines(path: Path, lineno: int) -> list[tuple[int, str, bool]]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []

    all_lines = text.splitlines()
    if not all_lines:
        return []

    start = max(1, lineno - _CONTEXT_LINES)
    end = min(len(all_lines), lineno + _CONTEXT_LINES)
    return [(num, all_lines[num - 1], num == lineno) for num in range(start, end + 1)]


def _sites_from_syntax_error(exc: TemplateSyntaxError) -> list[TemplateErrorSite]:
    path = _path_from_syntax_error(exc)
    line_text = ""
    if exc.source and exc.lineno:
        rows = exc.source.splitlines()
        if 0 < exc.lineno <= len(rows):
            line_text = rows[exc.lineno - 1]
    elif path.exists() and exc.lineno:
        for _num, text, is_err in _read_context_lines(path, exc.lineno):
            if is_err:
                line_text = text
                break

    return [
        TemplateErrorSite(
            path=path,
            lineno=exc.lineno or 1,
            location="template",
            line_text=line_text,
        )
    ]


def _sites_from_traceback(exc: BaseException) -> list[TemplateErrorSite]:
    sites: list[TemplateErrorSite] = []
    seen: set[tuple[str, int, str]] = set()
    tb: TracebackType | None = exc.__traceback__
    while tb is not None:
        frame = tb.tb_frame
        filename = frame.f_code.co_filename
        if _is_template_frame(filename, frame.f_code.co_name):
            path = Path(filename).resolve()
            key = (str(path), tb.tb_lineno, frame.f_code.co_name)
            if key not in seen:
                seen.add(key)
                line_text = ""
                for _num, text, is_err in _read_context_lines(path, tb.tb_lineno):
                    if is_err:
                        line_text = text
                        break
                sites.append(
                    TemplateErrorSite(
                        path=path,
                        lineno=tb.tb_lineno,
                        location=frame.f_code.co_name,
                        line_text=line_text,
                    )
                )
        tb = tb.tb_next
    return sites


def _path_from_syntax_error(exc: TemplateSyntaxError) -> Path:
    raw = exc.filename or exc.name or "<unknown>"
    if raw == "<unknown>":
        return Path(raw)
    return Path(raw).resolve()


def _is_template_frame(filename: str, location_name: str) -> bool:
    normalized = filename.replace("\\", "/")
    if "/site-packages/jinja2/" in normalized:
        return False
    if location_name in {"<module>", "<string>"}:
        return False
    if any(normalized.endswith(suffix) for suffix in _TEMPLATE_SUFFIXES):
        return True
    if location_name == "template":
        return True
    if "template code" in location_name:
        return True
    if location_name.startswith("block_"):
        return True
    return False


def _exception_message(exc: BaseException) -> str:
    if isinstance(exc, TemplateError):
        msg = exc.message
        if msg:
            return str(msg)
    return str(exc) or type(exc).__name__


def _cause_messages(exc: BaseException) -> list[str]:
    messages: list[str] = []
    current = exc.__cause__ or exc.__context__
    while current is not None and current is not exc:
        if isinstance(current, TemplateError):
            current = current.__cause__ or current.__context__
            continue
        text = str(current).strip()
        label = f"{type(current).__name__}: {text}"
        if text and label not in messages:
            messages.append(label)
        current = current.__cause__ or current.__context__
    return messages


__all__ = [
    "TemplateErrorReport",
    "TemplateErrorSite",
    "build_template_error_report",
    "print_template_error",
]
