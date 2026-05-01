import difflib
import sys
import tempfile
import zipfile
from pathlib import Path

CLI_ROOT = Path(__file__).resolve().parents[2] / "cli"
if str(CLI_ROOT) not in sys.path:
    sys.path.insert(0, str(CLI_ROOT))

from _core import Core  # noqa: E402

from ._errors import ConfigSizeError, RenderNoOutput, TemplateNotFound
from ._models import MAX_CONFIG_FILE_BYTES, DownloadFile, UploadedFile


class TemplateServer:
    """用固定模板根目录处理远程文件渲染请求。"""

    def __init__(self, template_root: str | Path) -> None:
        """保存服务端允许使用的模板根目录。

        Args:
            template_root: 服务端部署时指定的模板根目录
        """
        self.template_root = Path(template_root).resolve()
        if not self.template_root.exists():
            raise FileNotFoundError(self.template_root)

    def render(self, fields: dict[str, str], uploaded_input: UploadedFile | None) -> DownloadFile:
        """按上传文件执行一次渲染，并返回生成文件。

        Args:
            fields: 表单里的渲染参数
            uploaded_input: 调用方上传的输入配置
        """
        template_path = self.resolve_template(fields.get("template"))
        models_filename = self._optional_text(fields, "models_filename") or "models.py"

        with tempfile.TemporaryDirectory(prefix="jinja_build_server_") as tmp:
            work_root = Path(tmp)
            input_path = self._save_input(work_root, uploaded_input)
            output_path = self._output_target(work_root, template_path)
            Core(
                template=str(template_path),
                input=input_path,
                output=str(output_path),
                models_filename=models_filename,
            ).run()
            return self._build_download(template_path, output_path)

    def resolve_template(self, value: object) -> Path:
        """把外部模板名解析到服务端模板根目录内。"""
        if not isinstance(value, str) or not value.strip():
            raise TypeError("template must be a relative path")
        relative = Path(value)
        if relative.is_absolute() or ".." in relative.parts:
            raise TypeError("template must stay inside template root")

        template_path = (self.template_root / relative).resolve()
        if not self._is_inside_root(template_path) or not template_path.exists():
            suggestion = self.suggest_template(value)
            raise TemplateNotFound(f"template not found: {value}", suggestion)
        return template_path

    def suggest_template(self, value: str) -> str | None:
        """从可用模板路径里找一个相近名字。"""
        candidates = self._template_candidates()
        matches = difflib.get_close_matches(value, candidates, n=1, cutoff=0.0)
        return matches[0] if matches else None

    def _template_candidates(self) -> list[str]:
        """列出外部可以选择的相对模板路径。"""
        candidates = ["."]
        for path in self.template_root.rglob("*"):
            if path.is_dir() or path.suffix == ".j2":
                candidates.append(path.relative_to(self.template_root).as_posix())
        return candidates

    def _is_inside_root(self, path: Path) -> bool:
        """判断路径是否仍在模板根目录内。"""
        try:
            path.relative_to(self.template_root)
        except ValueError:
            return False
        return True

    def _optional_text(self, payload: dict[str, str], key: str) -> str | None:
        """读取可选文本字段。"""
        value = payload.get(key)
        if value is None:
            return None
        if not value:
            raise TypeError(f"{key} must be a non-empty string")
        return value

    def _save_input(self, work_root: Path, uploaded_input: UploadedFile | None) -> str | None:
        """把上传配置保存到本次请求的临时目录。"""
        if uploaded_input is None:
            return None

        self._check_config_size(uploaded_input.content)
        input_dir = work_root / "input"
        input_dir.mkdir()
        filename = Path(uploaded_input.filename).name or "input"
        input_path = input_dir / filename
        input_path.write_bytes(uploaded_input.content)
        return str(input_path)

    def _output_target(self, work_root: Path, template_path: Path) -> Path:
        """为本次渲染准备临时输出位置。"""
        if template_path.is_dir():
            return work_root / "output"
        return work_root / template_path.with_suffix("").name

    def _build_download(self, template_path: Path, output_path: Path) -> DownloadFile:
        """把渲染结果整理成下载文件。"""
        if template_path.is_dir():
            return DownloadFile(
                filename=f"{template_path.name or 'output'}.zip",
                content_type="application/zip",
                content=self._zip_output(output_path),
            )
        if not output_path.exists():
            raise RenderNoOutput("render produced no output")
        return DownloadFile(
            filename=output_path.name,
            content_type="application/octet-stream",
            content=output_path.read_bytes(),
        )

    def _zip_output(self, output_path: Path) -> bytes:
        """把目录输出压成一个 zip 文件。"""
        with tempfile.TemporaryFile() as tmp:
            with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as archive:
                if output_path.exists():
                    for path in output_path.rglob("*"):
                        if path.is_file():
                            archive.write(path, path.relative_to(output_path).as_posix())
            tmp.seek(0)
            return tmp.read()

    def _check_config_size(self, content: bytes) -> None:
        """检查上传配置文件大小是否像正常配置。"""
        size = len(content)
        if size == 0 or size > MAX_CONFIG_FILE_BYTES:
            raise ConfigSizeError("input config size is abnormal")
