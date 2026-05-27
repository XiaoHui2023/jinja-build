from rich.console import Console
from rich.theme import Theme

JINJA_ERROR_THEME = Theme(
    {
        "error.title": "#dc2626",
        "error.path": "#2563eb",
        "error.line_no": "#d97706",
        "error.line_body": "#6b7280",
        "error.line_highlight": "#ca8a04",
        "error.caret": "#dc2626",
        "error.dim": "#71717a",
        "error.label": "#9333ea",
        "error.message": "#3f3f46",
    }
)

_console: Console | None = None


def jinja_error_console() -> Console:
    """返回用于模板错误输出的 Rich 控制台（固定 hex 主题）。"""
    global _console
    if _console is None:
        _console = Console(
            theme=JINJA_ERROR_THEME,
            color_system="truecolor",
            force_terminal=True,
            legacy_windows=False,
        )
    return _console


__all__ = [
    "JINJA_ERROR_THEME",
    "jinja_error_console",
]
