from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RenderFailure(Exception):
    """并行渲染中单次失败；由 Core 汇总后只展示一张错误卡片。"""

    exc: BaseException
    entry_path: Path

    def __str__(self) -> str:
        return str(self.exc)


class AlreadyReportedError(Exception):
    """终端已用 Rich 展示过的用户侧错误，入口层应直接退出。"""

    def __init__(self, source: BaseException | None = None) -> None:
        self.source = source
        super().__init__()


def raise_after_report(exc: BaseException) -> None:
    """在 Rich 输出后抛出，避免解释器再打印默认 traceback。"""
    raise AlreadyReportedError(exc) from None


__all__ = [
    "AlreadyReportedError",
    "RenderFailure",
    "raise_after_report",
]
