from __future__ import annotations


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
    "raise_after_report",
]
