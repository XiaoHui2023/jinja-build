from .load_input import load_input, load_json, load_yaml
from .load_filter import load_filter
from .load_filelist import LoadFileList
from _utils import jinja
import inspect
import builtins
from pathlib import Path
from typing import Dict, List, Optional, Type, Any
from typeguard import typechecked
from pydantic import BaseModel


class Core(BaseModel):
    template: str
    input: Optional[str]
    output: str
    models_filename: Optional[str] = None
    filelist_filename: Optional[str] = None

    template_path: Path = None
    """模板目录路径"""
    filelist_path: Optional[Path] = None
    """文件列表文件路径"""
    models_path: Path = None
    """数据文件路径"""

    input_model: Type[Any] = None
    """输入类型"""
    input_data: dict = None
    """输入data dict"""
    global_data: dict = None
    """全局数据"""

    def model_post_init(self, ctx):
        if not self.template:
            raise Exception("require template")
        self.template_path = Path(self.template)

        if not self.models_filename:
            self.models_filename = "models.py"

        if not self.filelist_filename:
            self.filelist_filename = "filelist.yaml"

        # filelist路径
        self.filelist_path = self.template_path / self.filelist_filename
        if not self.filelist_path.exists():
            self.filelist_path = None

        # models路径
        self.models_path = self.template_path / self.models_filename
        if not self.models_path.exists():
            raise FileNotFoundError(models_path)

    def run(self):
        self._load_input()
        self._load_template()

    def _load_template(self):
        # 模板目录 / 单个模板文件
        if self.template_path.is_dir():
            search_paths = [self.template_path]
            file_map = LoadFileList(self.template_path, self.filelist_path, self.input_data, self.output).run()
        else:
            search_paths = []
            file_map = {self.template: self.output}

        # 生成 jinja
        for path_j2, dst in file_map.items():
            content = jinja.render(path_j2, self.input_model, self.global_data, search_paths=search_paths)
            self.write_output(dst, content)

    def _load_input(self):
        if self.input:
            self.input_data = load_input(self.input)
        else:
            self.input_data = None
        if not self.input_data:
            self.input_data = {}

        # 加载models
        try:
            class_map = jinja.load_models(self.models_path)
        except:
            print(f"Invalid models file: {self.models_path}")
            raise
        models_type = class_map[-1]
        self.input_model = models_type(**self.input_data)
        self.input_data = jinja.to_dict(self.input_model)

        # 获取模板目录下所有脚本名
        root_scripts = list(set([Path(x).parts[1].stem for x in self.template_path.rglob("*.py")]))

        # 得到主类所有内置函数
        main_builtins = [x for x in self.input_model.__class__.__mro__ if x.__module__.split(".")[0] not in root_scripts]

        # 得到主类所有内置函数名
        main_builtin_func_names = [name for cls in main_builtins for name, func in inspect.getmembers(cls, predicate=inspect.isfunction)]

        # 得到主类所有对外开放，非内置的函数
        main_export_func_map = {name: func for name, func in inspect.getmembers(models_type, predicate=inspect.isfunction) if not name.startswith("_") and name not in main_builtin_func_names}

        # 得到系统所有内置函数
        sys_builtin_funcs = {name: obj for name, obj in vars(builtins).items() if inspect.isbuiltin(obj) or inspect.isfunction(obj)}

        # 类、顶层函数、输入全局
        self.global_data = sys_builtin_funcs | {
            x.__name__: x for x in class_map
        } | {
            name: lambda *args, **kwargs: func(self.input_model, *args, **kwargs) for name, func in main_export_func_map.items()
        }

    def write_output(self, dst: str, data: str):
        Path(dst).parent.mkdir(parents=True, exist_ok=True)

        with open(dst, "w", encoding="utf-8") as f:
            f.write(data)
            print(f"output: {dst}")


__all__ = [
    "load_input",
    "load_json",
    "load_yaml",
    "load_filter",
    "LoadFileList",
]
