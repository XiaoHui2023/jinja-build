import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def _env(name: str, default: str) -> str:
    """读取容器运行参数。"""
    return os.getenv(name, default)


def _ensure_dirs(*paths: str) -> None:
    """准备容器内需要写入的目录。"""
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)


def _start_processes() -> list[subprocess.Popen[bytes]]:
    """同时启动服务端和文档生成器。"""
    port = _env("PORT", "8000")
    template_dir = _env("TEMPLATE_DIR", "/data/template")
    doc_dir = _env("DOC_DIR", "/data/doc")
    log_dir = _env("LOG_DIR", "/data/log")
    models_filename = _env("MODELS_FILENAME", "models.py")
    doc_interval = _env("DOC_INTERVAL", "1.0")

    _ensure_dirs(doc_dir, str(Path(log_dir) / "server"), str(Path(log_dir) / "doc"))

    return [
        subprocess.Popen(
            [
                sys.executable,
                "server/__main__.py",
                "-p",
                port,
                "-t",
                template_dir,
                "-l",
                str(Path(log_dir) / "server"),
            ],
        ),
        subprocess.Popen(
            [
                sys.executable,
                "doc/__main__.py",
                "-t",
                template_dir,
                "-o",
                doc_dir,
                "-l",
                str(Path(log_dir) / "doc"),
                "-mf",
                models_filename,
                "-i",
                doc_interval,
            ],
        ),
    ]


def _stop_processes(processes: list[subprocess.Popen[bytes]]) -> None:
    """停止仍在运行的子进程。"""
    for process in processes:
        if process.poll() is None:
            process.terminate()
    for process in processes:
        if process.poll() is None:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()


def main() -> int:
    """把服务端和文档生成器放在同一个容器生命周期里。"""
    processes = _start_processes()

    def handle_stop(signum: int, frame: object) -> None:
        _stop_processes(processes)
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, handle_stop)
    signal.signal(signal.SIGINT, handle_stop)

    while True:
        for process in processes:
            code = process.poll()
            if code is not None:
                _stop_processes(processes)
                return code
        time.sleep(1)


if __name__ == "__main__":
    raise SystemExit(main())
