from rich.console import Console
from rich.theme import Theme

JINJA_ERROR_THEME = Theme(
    {
        "error.title": "#e06c75",
        "error.path": "#61afef",
        "error.line_no": "#d19a66",
        "error.line_body": "#abb2bf",
        "error.line_highlight": "#e5c07b",
        "error.caret": "#e06c75",
        "error.dim": "#5c6370",
        "error.label": "#c678dd",
        "error.message": "#dcdfe4",
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
