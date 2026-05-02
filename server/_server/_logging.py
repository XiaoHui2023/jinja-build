import logging
from datetime import datetime
from pathlib import Path


LOGGER_NAME = "jinja_build.server"


def configure_logging(log_dir: str | Path) -> tuple[logging.Logger, Path]:
    """配置服务端文件日志，并返回本次写入的文件。"""
    path = _log_path(log_dir)
    path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    for handler in logger.handlers:
        handler.close()
    logger.handlers.clear()
    logger.propagate = False

    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"),
    )
    logger.addHandler(handler)
    return logger, path


def _log_path(log_dir: str | Path) -> Path:
    """按日期和时间生成日志文件路径。"""
    now = datetime.now()
    return Path(log_dir) / now.strftime("%Y-%m-%d") / f"{now.strftime('%H-%M-%S')}.log"


def get_logger() -> logging.Logger:
    """取得服务端日志对象。"""
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
    return logger
