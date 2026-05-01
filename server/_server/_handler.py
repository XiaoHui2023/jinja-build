import json
from email.parser import BytesParser
from email.policy import default
from http.server import BaseHTTPRequestHandler
from urllib.parse import quote

from pydantic import ValidationError

from ._app import TemplateServer
from ._errors import ConfigSizeError, RenderNoOutput, TemplateNotFound
from ._logging import get_logger
from ._models import DownloadFile, UploadedFile


def make_handler(app: TemplateServer) -> type[BaseHTTPRequestHandler]:
    """创建绑定服务对象的请求处理器。"""
    logger = get_logger()

    class RenderHandler(BaseHTTPRequestHandler):
        """处理远程渲染请求。"""

        def do_POST(self) -> None:
            """处理渲染请求。"""
            logger.info("request start client=%s path=%s", self.client_address[0], self.path)
            if self.path != "/render":
                logger.warning("request rejected client=%s status=404 reason=not_found", self.client_address[0])
                self._write_json(404, {"ok": False, "error": "not found"})
                return

            try:
                fields, uploaded_input = self._read_multipart()
                logger.info(
                    "render start client=%s template=%s input=%s input_bytes=%s",
                    self.client_address[0],
                    fields.get("template"),
                    uploaded_input.filename if uploaded_input else None,
                    len(uploaded_input.content) if uploaded_input else 0,
                )
                download = app.render(fields, uploaded_input)
            except TemplateNotFound as error:
                logger.warning(
                    "render rejected client=%s status=404 error=%s suggestion=%s",
                    self.client_address[0],
                    error,
                    error.suggestion,
                )
                self._write_json(
                    404,
                    {"ok": False, "error": str(error), "did_you_mean": error.suggestion},
                )
                return
            except RenderNoOutput as error:
                logger.warning("render rejected client=%s status=422 error=%s", self.client_address[0], error)
                self._write_json(422, {"ok": False, "error": str(error)})
                return
            except ConfigSizeError as error:
                logger.warning("render rejected client=%s status=400 error=%s", self.client_address[0], error)
                self._write_json(400, {"ok": False, "error": str(error)})
                return
            except (TypeError, ValueError, ValidationError) as error:
                logger.warning("render rejected client=%s status=400 error=%s", self.client_address[0], error)
                self._write_json(400, {"ok": False, "error": str(error)})
                return
            except Exception as error:
                logger.exception("render failed client=%s status=500 error=%s", self.client_address[0], error)
                self._write_json(500, {"ok": False, "error": str(error)})
                return

            self._write_download(download)
            logger.info(
                "render success client=%s status=200 filename=%s bytes=%s",
                self.client_address[0],
                download.filename,
                len(download.content),
            )

        def log_message(self, format: str, *args: object) -> None:
            """保持服务输出简洁。"""

        def _read_multipart(self) -> tuple[dict[str, str], UploadedFile | None]:
            """读取上传表单里的参数和输入文件。"""
            content_type = self.headers.get("Content-Type", "")
            if not content_type.startswith("multipart/form-data"):
                raise TypeError("request must be multipart/form-data")

            length = self._content_length()
            raw = self.rfile.read(length)
            message = BytesParser(policy=default).parsebytes(
                f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8") + raw,
            )
            if not message.is_multipart():
                raise TypeError("request must be multipart/form-data")

            fields: dict[str, str] = {}
            uploaded_input: UploadedFile | None = None
            for part in message.iter_parts():
                name = part.get_param("name", header="content-disposition")
                if not name:
                    continue
                filename = part.get_filename()
                content = part.get_payload(decode=True) or b""
                if filename is None:
                    fields[name] = content.decode(part.get_content_charset() or "utf-8")
                elif name == "input":
                    if uploaded_input is not None:
                        raise TypeError("input file can only be uploaded once")
                    uploaded_input = UploadedFile(filename=filename, content=content)
                else:
                    raise TypeError(f"unexpected file field: {name}")
            return fields, uploaded_input

        def _content_length(self) -> int:
            """读取请求体长度。"""
            try:
                return int(self.headers.get("Content-Length", "0"))
            except ValueError as error:
                raise ValueError("content length must be an integer") from error

        def _write_download(self, download: DownloadFile) -> None:
            """把渲染结果作为附件写回调用方。"""
            content_disposition = self._content_disposition(download.filename)
            self.send_response(200)
            self.send_header("Content-Type", download.content_type)
            self.send_header("Content-Length", str(len(download.content)))
            self.send_header("Content-Disposition", content_disposition)
            self.end_headers()
            self.wfile.write(download.content)

        def _content_disposition(self, filename: str) -> str:
            """生成兼容常见客户端的附件文件名。"""
            ascii_name = filename.encode("ascii", "ignore").decode("ascii") or "output"
            escaped = ascii_name.replace("\\", "_").replace('"', "_")
            return f'attachment; filename="{escaped}"; filename*=UTF-8\'\'{quote(filename)}'

        def _write_json(self, status: int, body: dict[str, object]) -> None:
            """写出 JSON 响应。"""
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return RenderHandler
