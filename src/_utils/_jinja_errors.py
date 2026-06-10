from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import TracebackType

from jinja2.exceptions import TemplateError, TemplateNotFound, TemplateSyntaxError
from rich.console import Group
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from ._error_card import error_title, hints_block, meta_grid, print_error_card
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
        sites.extend(_innermost_template_sites(_sites_from_traceback(exc)))

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


def build_render_user_error_report(
    exc: BaseException,
    entry_path: Path | None = None,
) -> TemplateErrorReport:
    """从渲染期用户 Python 异常收集模板位置与 models 等用户代码位置。"""
    message = _exception_message(exc)
    extra = list(_cause_messages(exc))
    user_sites = _collect_user_sites(exc)
    template_sites = _innermost_template_sites(_sites_from_traceback(exc))
    sites = list(user_sites)
    seen = {(str(site.path), site.lineno) for site in sites}
    for site in template_sites:
        key = (str(site.path), site.lineno)
        if key in seen:
            continue
        seen.add(key)
        sites.append(site)

    if entry_path is not None and not template_sites:
        entry_site = _entry_template_site(entry_path)
        key = (str(entry_site.path), entry_site.lineno)
        if key not in seen:
            sites.append(entry_site)

    return TemplateErrorReport(
        exc_type=type(exc).__name__,
        message=message,
        entry_path=entry_path.resolve() if entry_path else None,
        sites=tuple(sites),
        extra=tuple(extra),
    )


def _print_error_report(report: TemplateErrorReport) -> None:
    console = jinja_error_console()

    body: list[object] = []
    if report.entry_path is not None:
        body.append(
            meta_grid([("入口模板", str(report.entry_path), "error.path")]),
        )

    sites_group = _sites_group(report.sites)
    if sites_group is not None:
        body.append(sites_group)

    hints = hints_block(report.extra)
    if hints is not None:
        body.append(hints)

    print_error_card(
        console,
        title=error_title(report.exc_type, report.message),
        body_parts=body,
        context=None,
    )


def print_template_error(
    exc: BaseException,
    entry_path: Path | None = None,
) -> None:
    """用 Rich 打印模板错误（仅含模板相关位置）。"""
    report = build_template_error_report(exc, entry_path=entry_path)
    _print_error_report(report)


def print_render_user_error(
    exc: BaseException,
    entry_path: Path | None = None,
) -> None:
    """用 Rich 打印渲染期 models 代码或 property 求值错误。"""
    report = build_render_user_error_report(exc, entry_path=entry_path)
    _print_error_report(report)


def _sites_group(sites: tuple[TemplateErrorSite, ...]) -> Group | None:
    if not sites:
        return None
    parts: list[Text | Rule | Group] = []
    for index, site in enumerate(sites):
        if index > 0:
            parts.append(Rule(style="error.dim"))
        block = _site_context_group(site)
        if block is not None:
            parts.append(block)
    return Group(*parts) if parts else None


def _site_header(site: TemplateErrorSite) -> Text:
    header = Text()
    header.append(str(site.path), style="error.path")
    if site.lineno >= 1:
        header.append(f":{site.lineno}", style="error.line_no")
    location = _format_site_location(site.location)
    if location:
        header.append(f"  ({location})", style="error.dim")
    return header


def _site_context_group(site: TemplateErrorSite) -> Group | None:
    header = _site_header(site)

    if site.lineno < 1:
        return Group(header)

    rows = _read_context_lines(site.path, site.lineno)
    line_parts: list[Text] = [header]
    if not rows and site.line_text:
        line_parts.append(
            Text.assemble(
                (f"{site.lineno:>4} ", "error.line_no"),
                (site.line_text.rstrip(), "error.line_highlight"),
            )
        )
        return Group(*line_parts)

    for num, text, is_error in rows:
        style = "error.line_highlight" if is_error else "error.line_body"
        line_parts.append(
            Text.assemble(
                (f"{num:>4} ", "error.line_no"),
                (text.rstrip("\n"), style),
            )
        )
    return Group(*line_parts)


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


_INTERNAL_FRAME_MARKERS = (
    "/site-packages/",
    "/concurrent/futures/",
    "/Lib/importlib/",
)
_INTERNAL_FRAME_SUFFIXES = (
    "/_utils/_jinja.py",
    "/_utils/_jinja_view.py",
    "/_utils/_jinja_convert.py",
    "/_utils/_jinja_env.py",
    "/_utils/_jinja_errors.py",
    "/_utils/_jinja_rich.py",
    "/_utils/_dynamic_loading.py",
    "/_utils/_filters.py",
    "/_utils/_cli_user_error.py",
    "/_utils/_input_errors.py",
    "/_utils/_error_card.py",
    "/_utils/_config_bundle.py",
    "/_core.py",
)


def _is_internal_python_frame(filename: str) -> bool:
    normalized = filename.replace("\\", "/")
    if not normalized.endswith(".py"):
        return True
    for marker in _INTERNAL_FRAME_MARKERS:
        if marker in normalized:
            return True
    for suffix in _INTERNAL_FRAME_SUFFIXES:
        if suffix in normalized:
            return True
    if "/_MEI" in normalized and "/_utils/" in normalized:
        return True
    return False


def _is_user_code_frame(filename: str) -> bool:
    return not _is_internal_python_frame(filename)


def _exception_cause_chain(exc: BaseException) -> list[BaseException]:
    chain: list[BaseException] = []
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        chain.append(current)
        current = current.__cause__
    return chain


def _collect_user_sites(exc: BaseException) -> list[TemplateErrorSite]:
    sites: list[TemplateErrorSite] = []
    seen: set[tuple[str, int]] = set()
    for linked in _exception_cause_chain(exc):
        for site in _sites_from_user_code_traceback(linked):
            key = (str(site.path), site.lineno)
            if key in seen:
                continue
            seen.add(key)
            sites.append(site)
    return sites


def _entry_template_site(entry_path: Path) -> TemplateErrorSite:
    path = entry_path.resolve()
    lineno = 1
    line_text = ""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        if lines:
            line_text = lines[0]
    except OSError:
        pass
    return TemplateErrorSite(
        path=path,
        lineno=lineno,
        location="模板",
        line_text=line_text,
    )


def _innermost_template_sites(sites: list[TemplateErrorSite]) -> list[TemplateErrorSite]:
    if len(sites) <= 1:
        return sites
    return [sites[-1]]


def _format_site_location(location: str) -> str:
    if not location:
        return ""
    if "template code" in location:
        return "模板"
    if location == "template":
        return "模板"
    return location


def _sites_from_user_code_traceback(exc: BaseException) -> list[TemplateErrorSite]:
    sites: list[TemplateErrorSite] = []
    seen: set[tuple[str, int, str]] = set()
    tb: TracebackType | None = exc.__traceback__
    while tb is not None:
        frame = tb.tb_frame
        filename = frame.f_code.co_filename
        if _is_user_code_frame(filename):
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
    headline = _exception_message(exc)
    messages: list[str] = []
    for current in _exception_cause_chain(exc)[1:]:
        if isinstance(current, TemplateError):
            continue
        text = str(current).strip()
        if not text:
            continue
        label = f"{type(current).__name__}: {text}"
        if label in messages or text in headline:
            continue
        messages.append(label)
    return messages


__all__ = [
    "TemplateErrorReport",
    "TemplateErrorSite",
    "build_render_user_error_report",
    "build_template_error_report",
    "print_render_user_error",
    "print_template_error",
]
