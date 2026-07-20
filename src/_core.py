import inspect
import json
import os
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from configlib import load_config
from pydantic import BaseModel, ConfigDict, Field

from _utils import jinja
from jinja2.exceptions import TemplateError

from _utils._cli_user_error import RenderFailure, raise_after_report
from _utils._config_bundle import load_bundle_config
from _utils._dynamic_loading import models_import_path
from _utils._filters import build_model_method_filters
from _utils._input_errors import print_input_model_error
from _utils._jinja_errors import print_render_user_error, print_template_error


class Core(BaseModel):
    """把配置数据套进模板目录，生成一组输出文件。"""

    model_config = ConfigDict(extra="forbid")

    template: str = Field(description="模板目录。")
    input: str | None = Field(default=None, description="输入配置文件或配置文件目录，省略时按空配置处理。")
    output: str = Field(description="输出文件或目录。")
    models_filename: str = Field(default="models.py", description="模板目录中的数据结构文件。")
    debug_input: str | None = Field(
        default=None,
        description="将配置文件解析结果写出为指定 JSON 路径（尚未实例化 models）。",
    )
    debug_models: str | None = Field(
        default=None,
        description="将 models 实例化后的模板数据写出为指定 JSON 路径（渲染前）。",
    )

    template_path: Path | None = None
    """模板目录路径"""
    models_path: Path | None = None
    """数据文件路径"""

    def model_post_init(self, ctx: object) -> None:
        """准备模板目录与数据结构文件路径。"""
        if not self.template:
            raise Exception("require template")
        self.template_path = Path(self.template)
        if not self.template_path.exists():
            raise FileNotFoundError(self.template_path)
        if not self.template_path.is_dir():
            raise NotADirectoryError(self.template_path)

        self.models_path = self.template_path / self.models_filename
        if not self.models_path.exists():
            raise FileNotFoundError(self.models_path)

    def run(self) -> None:
        """加载输入配置并渲染模板。"""
        if self.models_path is None:
            raise RuntimeError("models path is not ready")
        with models_import_path(self.models_path):
            input_outputs = self._iter_input_outputs()
            class_map = self._load_models()
            inputs = self._load_inputs(class_map, input_outputs)
            templates = self._load_template_paths()
            self._render_all(inputs, templates)

    def _load_template_paths(self) -> tuple[list[Path], list[Path]]:
        """读取需要渲染的模板文件和搜索目录。"""
        if self.template_path is None:
            raise RuntimeError("template path is not ready")

        return list(self.template_path.rglob("*.j2")), [self.template_path]

    def _load_models(self) -> list[type]:
        """读取数据结构文件。"""
        if self.models_path is None:
            raise RuntimeError("models path is not ready")
        try:
            return jinja.load_models(self.models_path)
        except:
            print(f"Invalid models file: {self.models_path}")
            raise

    def _load_inputs(
        self,
        class_map: list[type],
        input_outputs: list[tuple[str | None, Path, str | None]],
    ) -> list[tuple[object, dict[str, object], dict[str, object], Path]]:
        """读取全部输入配置并创建模板可用的数据对象。"""
        models_type = class_map[-1]
        return [
            self._build_input(models_type, class_map, input_path, output_path, debug_name)
            for input_path, output_path, debug_name in input_outputs
        ]

    def _iter_input_outputs(self) -> list[tuple[str | None, Path, str | None]]:
        """展开单次输入或目录输入。"""
        output_root = Path(self.output)
        if not self.input:
            return [(None, output_root, None)]

        input_path = Path(self.input)
        if not input_path.exists():
            raise FileNotFoundError(input_path)
        if input_path.is_file():
            return [(self.input, output_root, None)]
        if not input_path.is_dir():
            raise ValueError(f"Input path must be a file or directory: {input_path}")

        inputs = sorted(path for path in input_path.iterdir() if path.is_file())
        self._check_input_names(inputs)
        return [(str(path), output_root / path.stem, path.stem) for path in inputs]

    def _check_input_names(self, inputs: list[Path]) -> None:
        """检查目录输入展开后的输出目录名是否重复。"""
        seen = set()
        duplicates = set()
        for input_path in inputs:
            name = input_path.stem
            if name in seen:
                duplicates.add(name)
            seen.add(name)
        if duplicates:
            raise ValueError(f"Duplicate input output name: {', '.join(sorted(duplicates))}")

    def _build_input(
        self,
        models_type: type,
        class_map: list[type],
        input_path: str | None,
        output_path: Path,
        debug_name: str | None,
    ) -> tuple[object, dict[str, object], dict[str, object], Path]:
        """把一个配置文件转换成一次渲染需要的数据。"""
        if self.models_path is None:
            raise RuntimeError("models path is not ready")
        models_path = self.models_path
        resolved_input = Path(input_path).resolve() if input_path else None
        try:
            input_data = self._load_input_data(input_path)
        except BaseException as exc:
            print_input_model_error(
                exc,
                input_path=resolved_input,
                models_path=models_path,
                models_type=models_type,
                stage="config",
            )
            raise_after_report(exc)
        if self.debug_input:
            self._write_debug_json(
                self._resolve_debug_path(self.debug_input, debug_name),
                input_data,
            )
        try:
            input_model = models_type(**input_data)
        except BaseException as exc:
            print_input_model_error(
                exc,
                input_path=resolved_input,
                models_path=models_path,
                models_type=models_type,
                stage="model",
            )
            raise_after_report(exc)
        if self.debug_models:
            self._write_debug_json(
                self._resolve_debug_path(self.debug_models, debug_name),
                jinja.to_dict(input_model),
            )
        globals_data, filters_data = self._build_template_extras(class_map, input_model)
        return input_model, globals_data, filters_data, output_path

    def _load_input_data(self, input_path: str | None) -> dict[str, object]:
        """读取一个输入配置文件。"""
        if not input_path:
            return {}

        path = Path(input_path).resolve()
        loaded = load_bundle_config(path)
        if loaded is None:
            loaded = load_config(path)
        if loaded is None:
            return {}
        if isinstance(loaded, Mapping):
            return dict(loaded)
        raise TypeError(f"Input config must be a mapping, got {type(loaded).__name__}")

    def _build_template_extras(
        self,
        class_map: list[type],
        input_model: object,
    ) -> tuple[dict[str, object], dict[str, object]]:
        """准备模板全局函数与管道过滤器。"""
        models_type = class_map[-1]
        method_globals = {
            name: (lambda *args, _func=func, **kwargs: _func(input_model, *args, **kwargs))
            for name, func in vars(models_type).items()
            if inspect.isfunction(func) and not name.startswith("_")
        }
        globals_data = {cls.__name__: cls for cls in class_map} | method_globals
        filters_data = build_model_method_filters(models_type, input_model)
        return globals_data, filters_data

    def _render_all(
        self,
        inputs: list[tuple[object, dict[str, object], dict[str, object], Path]],
        templates: tuple[list[Path], list[Path]],
    ) -> None:
        """并行渲染全部输入和模板组合。"""
        template_paths, search_paths = templates
        jobs = [
            (
                path_j2,
                self._output_path(output_path, path_j2),
                input_model,
                global_data,
                filter_data,
                search_paths,
            )
            for input_model, global_data, filter_data, output_path in inputs
            for path_j2 in template_paths
        ]
        if not jobs:
            return

        max_workers = min(len(jobs), os.cpu_count() or 1)
        failures: list[RenderFailure] = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self._render_one, *job) for job in jobs]
            for future in as_completed(futures):
                try:
                    future.result()
                except RenderFailure as failure:
                    failures.append(failure)

        if failures:
            self._report_first_render_failure(failures)

    def _output_path(self, output_root: Path, path_j2: Path) -> str:
        """计算单个模板对应的输出路径。"""
        if self.template_path is None:
            raise RuntimeError("template path is not ready")
        return str(output_root / path_j2.relative_to(self.template_path).with_suffix(""))

    def _report_first_render_failure(self, failures: list[RenderFailure]) -> None:
        """并行渲染有多处失败时，只展示一张错误卡片。"""
        failure = min(failures, key=lambda item: str(item.entry_path))
        exc = failure.exc
        if isinstance(exc, TemplateError):
            print_template_error(exc, entry_path=failure.entry_path)
        else:
            print_render_user_error(exc, entry_path=failure.entry_path)
        raise_after_report(exc)

    def _render_one(
        self,
        path_j2: Path,
        dst: str,
        input_model: object,
        global_data: dict[str, object],
        filter_data: dict[str, object],
        search_paths: list[Path],
    ) -> None:
        """渲染并写出一个模板结果。"""
        try:
            content = jinja.render(
                path_j2,
                input_model,
                global_data,
                filters_var=filter_data,
                search_paths=search_paths,
                defer_error_report=True,
            )
        except Exception as exc:
            raise RenderFailure(exc, path_j2.resolve()) from None
        if not content.strip():
            return
        self.write_output(dst, content)

    def write_output(self, dst: str, data: str) -> None:
        """写出渲染后的内容。"""
        Path(dst).parent.mkdir(parents=True, exist_ok=True)

        with open(dst, "w", encoding="utf-8") as f:
            f.write(data)
            print(f"output: {dst}")

    def _resolve_debug_path(self, debug_path: str, debug_name: str | None) -> Path:
        """绝对路径原样使用；目录输入时把调试路径当作输出目录。"""
        path = Path(debug_path)
        if not path.is_absolute():
            path = Path.cwd() / path
        if debug_name:
            return path / f"{debug_name}.json"
        return path

    def _write_debug_json(self, path: Path, data: object) -> None:
        """把调试数据写成 JSON 文件。"""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        print(f"debug: {path}")


__all__ = [
    "Core",
]
