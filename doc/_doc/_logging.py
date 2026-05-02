import logging
from datetime import datetime
from pathlib import Path


def configure_logging(log_root: str | Path) -> Path:
    """把文档生成日志写到按时间分层的文件。"""
    now = datetime.now()
    log_path = Path(log_root) / now.strftime("%Y-%m-%d") / f"{now.strftime('%H-%M-%S')}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8")],
        force=True,
    )
    return log_path
