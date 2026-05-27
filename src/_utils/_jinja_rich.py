from __future__ import annotations

import os
from typing import Literal

from rich.console import Console
from rich.theme import Theme

ThemeMode = Literal["auto", "light", "dark", "none"]
BackgroundHint = Literal["dark", "light", "unknown"]

DARK_ERROR_THEME = Theme(
    {
        "error.title": "#f87171",
        "error.path": "#60a5fa",
        "error.line_no": "#fbbf24",
        "error.line_body": "#9ca3af",
        "error.line_highlight": "#facc15",
        "error.caret": "#f87171",
        "error.dim": "#9ca3af",
        "error.label": "#c084fc",
        "error.message": "#e5e7eb",
    }
)

LIGHT_ERROR_THEME = Theme(
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

# 兼容旧引用
JINJA_ERROR_THEME = LIGHT_ERROR_THEME

_console: Console | None = None
_configured_mode: ThemeMode | None = None


def normalize_theme_mode(value: str | None) -> ThemeMode:
    """把 CLI 等传入的取值规范为受支持的主题模式。"""
    if not value:
        return "auto"
    mode = value.strip().lower()
    if mode in ("auto", "light", "dark", "none"):
        return mode
    return "auto"


def detect_background() -> BackgroundHint:
    """无阻塞地推断终端背景：仅读 COLORFGBG，不做 stdin/OSC 查询。"""
    return _background_from_colorfgbg()


def resolve_background(mode: ThemeMode) -> Literal["dark", "light"]:
    """根据主题模式得到实际使用的背景配色方案。"""
    if mode == "dark":
        return "dark"
    if mode == "light":
        return "light"
    detected = detect_background()
    if detected == "light":
        return "light"
    return "dark"


def theme_for_background(background: Literal["dark", "light"]) -> Theme:
    return DARK_ERROR_THEME if background == "dark" else LIGHT_ERROR_THEME


def configure_jinja_error_theme(mode: str | ThemeMode | None = None) -> None:
    """在首次打印错误前设置主题（由入口传入 CLI 的 --theme，缺省为 auto）。"""
    global _console, _configured_mode
    resolved = normalize_theme_mode(mode if mode is not None else "auto")
    _configured_mode = resolved
    _console = _build_console(resolved)


def reset_jinja_error_console() -> None:
    """测试或重复初始化时清空控制台缓存。"""
    global _console, _configured_mode
    _console = None
    _configured_mode = None


def jinja_error_console() -> Console:
    """返回用于错误输出的 Rich 控制台。"""
    global _console
    if _console is None:
        configure_jinja_error_theme(None)
    return _console


def _build_console(mode: ThemeMode) -> Console:
    if mode == "none":
        return Console(
            no_color=True,
            force_terminal=True,
            legacy_windows=False,
        )
    background = resolve_background(mode)
    return Console(
        theme=theme_for_background(background),
        color_system="truecolor",
        force_terminal=True,
        legacy_windows=False,
    )


def _background_from_colorfgbg() -> BackgroundHint:
    raw = os.environ.get("COLORFGBG", "")
    if not raw:
        return "unknown"
    parts = raw.split(";")
    if len(parts) < 2:
        return "unknown"
    try:
        bg = int(parts[-1].split(",")[0])
    except ValueError:
        return "unknown"
    if 0 <= bg <= 7:
        return "dark"
    if 8 <= bg <= 15:
        return "light"
    return "unknown"


__all__ = [
    "BackgroundHint",
    "DARK_ERROR_THEME",
    "JINJA_ERROR_THEME",
    "LIGHT_ERROR_THEME",
    "ThemeMode",
    "configure_jinja_error_theme",
    "detect_background",
    "jinja_error_console",
    "normalize_theme_mode",
    "reset_jinja_error_console",
    "resolve_background",
    "theme_for_background",
]
