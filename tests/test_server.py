import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
import zipfile
from http.server import ThreadingHTTPServer
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "server"
if str(SERVER) not in sys.path:
    sys.path.insert(0, str(SERVER))

from _server import (  # noqa: E402
    ConfigSizeError,
    MAX_CONFIG_FILE_BYTES,
    TemplateNotFound,
    TemplateServer,
    UploadedFile,
    configure_logging,
    make_handler,
)


class ServerRenderTests(unittest.TestCase):
    """覆盖服务端文件上传和下载整理行为。"""

    def test_single_template_returns_rendered_file(self) -> None:
        """单模板请求会把渲染结果作为文件返回。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_model(root)
            (root / "hello.txt.j2").write_text("Hello {{ name }}", encoding="utf-8")
            server = TemplateServer(root)

            download = server.render(
                {"template": "hello.txt.j2"},
                UploadedFile("ada.json", self._json_bytes({"name": "Ada"})),
            )

            self.assertEqual(download.filename, "hello.txt")
            self.assertEqual(download.content, b"Hello Ada")

    def test_directory_template_returns_zip(self) -> None:
        """目录模板请求会把输出目录压成 zip 返回。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "site"
            nested = template / "nested"
            nested.mkdir(parents=True)
            self._write_model(template)
            (template / "index.html.j2").write_text("Hello {{ title() }}", encoding="utf-8")
            (nested / "name.txt.j2").write_text("{{ name }}", encoding="utf-8")
            server = TemplateServer(root)

            download = server.render(
                {"template": "site"},
                UploadedFile("ada.json", self._json_bytes({"name": "Ada"})),
            )

            self.assertEqual(download.filename, "site.zip")
            self.assertEqual(download.content_type, "application/zip")
            with zipfile.ZipFile(BytesIO(download.content)) as archive:
                self.assertEqual(archive.read("index.html"), b"Hello ADA")
                self.assertEqual(archive.read("nested/name.txt"), b"Ada")

    def test_missing_template_returns_suggestion(self) -> None:
        """模板路径错误时给出相近路径。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template_root = root / "templates"
            (template_root / "apps" / "demo").mkdir(parents=True)

            with self.assertRaises(TemplateNotFound) as error:
                TemplateServer(template_root).render({"template": "apps/dmeo"}, None)

            self.assertEqual(error.exception.suggestion, "apps/demo")

    def test_absolute_template_is_rejected(self) -> None:
        """外部不能用绝对路径绕过服务端模板根目录。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template_root = root / "templates"
            template_root.mkdir()

            with self.assertRaises(TypeError):
                TemplateServer(template_root).render({"template": str(root)}, None)

    def test_abnormal_config_size_is_rejected(self) -> None:
        """配置文件大小异常时提前拒绝请求。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_model(root)
            (root / "hello.txt.j2").write_text("Hello", encoding="utf-8")
            uploaded = UploadedFile("large.json", b" " * (MAX_CONFIG_FILE_BYTES + 1))

            with self.assertRaises(ConfigSizeError):
                TemplateServer(root).render({"template": "hello.txt.j2"}, uploaded)

    def test_http_render_endpoint_returns_zip(self) -> None:
        """外部可以通过 HTTP 上传输入并拿到输出文件。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template_root = root / "templates"
            app_template = template_root / "demo"
            app_template.mkdir(parents=True)
            self._write_model(app_template)
            (app_template / "name.txt.j2").write_text("{{ title() }}", encoding="utf-8")

            app = TemplateServer(template_root)
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(app))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            try:
                port = httpd.server_address[1]
                request = urllib.request.Request(
                    f"http://127.0.0.1:{port}/render",
                    data=self._multipart_body(
                        {
                            "template": "demo",
                            "input": ("input.json", self._json_bytes({"name": "web"})),
                        },
                    ),
                    headers={"Content-Type": "multipart/form-data; boundary=jinja-build-test"},
                    method="POST",
                )

                with urllib.request.urlopen(request, timeout=5) as response:
                    content = response.read()

                self.assertEqual(response.status, 200)
                self.assertEqual(response.headers["Content-Type"], "application/zip")
                with zipfile.ZipFile(BytesIO(content)) as archive:
                    self.assertEqual(archive.read("name.txt"), b"WEB")
            finally:
                httpd.shutdown()
                httpd.server_close()
                thread.join(timeout=5)

    def test_render_error_is_logged_and_server_keeps_running(self) -> None:
        """模板渲染报错会写日志，服务仍能处理后续请求。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log_dir = root / "logs"
            template_root = root / "templates"
            template_root.mkdir()
            logger, log_path = configure_logging(log_dir)
            (template_root / "models.py").write_text(
                "class Data:\n"
                "    def __init__(self, name=''):\n"
                "        self.name = name\n"
                "\n"
                "    def explode(self):\n"
                "        raise RuntimeError('template exploded')\n",
                encoding="utf-8",
            )
            (template_root / "bad.txt.j2").write_text("{{ explode() }}", encoding="utf-8")
            (template_root / "ok.txt.j2").write_text("{{ name }}", encoding="utf-8")

            app = TemplateServer(template_root)
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(app))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            try:
                port = httpd.server_address[1]
                bad_request = self._render_request(port, "bad.txt.j2", {"name": "Ada"})
                with self.assertRaises(urllib.error.HTTPError) as error:
                    urllib.request.urlopen(bad_request, timeout=5)
                self.assertEqual(error.exception.code, 500)

                ok_request = self._render_request(port, "ok.txt.j2", {"name": "Ada"})
                with urllib.request.urlopen(ok_request, timeout=5) as response:
                    self.assertEqual(response.read(), b"Ada")

                log_text = log_path.read_text(encoding="utf-8")
                self.assertIn("render failed", log_text)
                self.assertIn("RuntimeError: template exploded", log_text)
                self.assertEqual(log_path.parent.parent, log_dir)
                self.assertEqual(len(log_path.parent.name), 8)
                self.assertEqual(len(log_path.stem), 6)
                self.assertEqual(log_path.suffix, ".log")
            finally:
                httpd.shutdown()
                httpd.server_close()
                thread.join(timeout=5)
                for handler in logger.handlers:
                    handler.close()
                logger.handlers.clear()

    def _write_model(self, template: Path) -> None:
        """写入测试用的数据结构文件。"""
        (template / "models.py").write_text(
            "class Data:\n"
            "    def __init__(self, name=''):\n"
            "        self.name = name\n"
            "\n"
            "    def title(self):\n"
            "        return self.name.upper()\n",
            encoding="utf-8",
        )

    def _json_bytes(self, data: dict[str, object]) -> bytes:
        """把测试输入转成上传文件内容。"""
        return json.dumps(data).encode("utf-8")

    def _multipart_body(self, fields: dict[str, str | tuple[str, bytes]]) -> bytes:
        """创建测试用上传请求体。"""
        chunks: list[bytes] = []
        boundary = b"jinja-build-test"
        for name, value in fields.items():
            chunks.append(b"--" + boundary)
            if isinstance(value, tuple):
                filename, content = value
                chunks.append(
                    (
                        f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
                        "Content-Type: application/octet-stream\r\n"
                    ).encode("utf-8"),
                )
                chunks.append(content)
            else:
                chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n'.encode("utf-8"))
                chunks.append(value.encode("utf-8"))
        chunks.append(b"--" + boundary + b"--")
        return b"\r\n".join(chunks) + b"\r\n"

    def _render_request(
        self,
        port: int,
        template: str,
        input_data: dict[str, object],
    ) -> urllib.request.Request:
        """创建渲染接口测试请求。"""
        return urllib.request.Request(
            f"http://127.0.0.1:{port}/render",
            data=self._multipart_body(
                {
                    "template": template,
                    "input": ("input.json", self._json_bytes(input_data)),
                },
            ),
            headers={"Content-Type": "multipart/form-data; boundary=jinja-build-test"},
            method="POST",
        )


if __name__ == "__main__":
    unittest.main()
