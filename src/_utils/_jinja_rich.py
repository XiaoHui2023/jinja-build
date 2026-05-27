from __future__ import annotations

import os
import re
import sys
import threading
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

_OSC_BG_QUERY = "\x1b]11;?\x07"
_OSC_DETECT_TIMEOUT = 0.08

_console: Console | None = None
_configured_mode: ThemeMode | None = None


def normalize_theme_mode(value: str | None) -> ThemeMode:
    """把环境变量或 CLI 取值规范为受支持的主题模式。"""
    if not value:
        return "auto"
    mode = value.strip().lower()
    if mode in ("auto", "light", "dark", "none"):
        return mode
    return "auto"


def detect_background() -> BackgroundHint:
    """推断终端背景深浅；失败时返回 unknown（不含 JINJA_BUILD_THEME，由 configure 处理）。"""
    hint = _background_from_colorfgbg()
    if hint != "unknown":
        return hint

    return _background_from_osc11(_OSC_DETECT_TIMEOUT)


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
    """在首次打印错误前设置主题（CLI 或环境变量）。"""
    global _console, _configured_mode
    resolved = normalize_theme_mode(mode if mode is not None else os.environ.get("JINJA_BUILD_THEME"))
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


def _background_from_osc11(timeout: float) -> BackgroundHint:
    if os.environ.get("CI"):
        return "unknown"
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return "unknown"
    if os.name == "nt":
        response = _read_osc_response_windows(timeout)
    else:
        response = _read_osc_response_unix(timeout)
    if not response:
        return "unknown"
    luminance = _luminance_from_osc_response(response)
    if luminance is None:
        return "unknown"
    return "light" if luminance > 0.5 else "dark"


def _read_osc_response_unix(timeout: float) -> str | None:
    import select
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    chunks: list[str] = []
    try:
        tty.setcbreak(fd)
        sys.stdout.write(_OSC_BG_QUERY)
        sys.stdout.flush()
        deadline = _monotonic() + timeout
        while _monotonic() < deadline:
            remaining = deadline - _monotonic()
            if remaining <= 0:
                break
            ready, _, _ = select.select([sys.stdin], [], [], remaining)
            if not ready:
                break
            chunk = sys.stdin.read(64)
            if not chunk:
                break
            chunks.append(chunk)
            joined = "".join(chunks)
            if "\x07" in joined or "\x1b\\" in joined:
                break
    except OSError:
        return None
    finally:
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        except OSError:
            pass
    return "".join(chunks) if chunks else None


def _read_osc_response_windows(timeout: float) -> str | None:
    import msvcrt

    result: list[str] = []

    def reader() -> None:
        try:
            sys.stdout.write(_OSC_BG_QUERY)
            sys.stdout.flush()
            deadline = _monotonic() + timeout
            while _monotonic() < deadline:
                if msvcrt.kbhit():
                    result.append(msvcrt.getwche())
                    joined = "".join(result)
                    if "\x07" in joined or "\x1b\\" in joined:
                        break
        except OSError:
            return

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    thread.join(timeout + 0.02)
    return "".join(result) if result else None


def _luminance_from_osc_response(response: str) -> float | None:
    match = re.search(
        r"rgb:([0-9a-fA-F]+)/([0-9a-fA-F]+)/([0-9a-fA-F]+)",
        response,
    )
    if match:
        components = [_osc_rgb_component(match.group(i)) for i in range(1, 4)]
        r, g, b = components
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    match = re.search(r"#([0-9a-fA-F]{6})", response)
    if match:
        hex_rgb = match.group(1)
        r = int(hex_rgb[0:2], 16) / 255
        g = int(hex_rgb[2:4], 16) / 255
        b = int(hex_rgb[4:6], 16) / 255
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    return None


def _osc_rgb_component(raw: str) -> float:
    value = int(raw, 16)
    if len(raw) == 4:
        return value / 0xFFFF
    if len(raw) == 2:
        return value / 0xFF
    divisor = (16 ** len(raw)) - 1
    return value / divisor if divisor else 0.0


def _monotonic() -> float:
    import time

    return time.monotonic()


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
