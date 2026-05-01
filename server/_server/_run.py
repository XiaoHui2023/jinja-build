from http.server import ThreadingHTTPServer
from pathlib import Path

from ._app import TemplateServer
from ._handler import make_handler
from ._logging import configure_logging


def run_server(
    port: int,
    template_root: str | Path,
    log: str | Path,
) -> None:
    """启动模板渲染服务。"""
    logger, log_path = configure_logging(log)
    app = TemplateServer(template_root)
    httpd = ThreadingHTTPServer(("0.0.0.0", port), make_handler(app))
    logger.info(
        "server starting host=0.0.0.0 port=%s template_root=%s log=%s",
        port,
        app.template_root,
        log_path,
    )
    print(f"server listening on 0.0.0.0:{port}, template root: {app.template_root}")
    httpd.serve_forever()
