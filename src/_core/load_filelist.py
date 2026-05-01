from pathlib import Path
from _utils import YAML
from typing import List, Any, Dict, Optional

JINJA_SUFFIXS = [".jinja2", ".j2"]


class LoadFileList:
    def __init__(self, template_root: str, filelist_path: Optional[str], input_data: dict, output_root: str):
        self.template_root = Path(template_root)
        self.filelist_path = filelist_path
        self.input_data = input_data
        self.output_root = output_root

    def run(self) -> Dict[str, str]:
        """
        渲染filelist
        """
        templates = [str(file.relative_to(self.template_root)) for suffix in JINJA_SUFFIXS for file in self.template_root.rglob(f"*{suffix}")]
        dirs = [str(file.relative_to(self.template_root)) for file in self.template_root.rglob("**/")]

        data = self.load_filelist()
        self.check_filelist(data, templates + dirs)
        templates = self.manage_dirs(data, templates, dirs)
        templates = self.manage_files(data, templates)

        paths_j2 = [self.template_root / x for x in templates]

        file_map = {x: str(Path(self.output_root) / x.relative_to(self.template_root).with_suffix("")) for x in paths_j2}
        return file_map

    def check_filelist(self, data: dict, files: List[str]):
        """检查filelist中所模板的文件是否为jinja2模板或目录"""

        if not self.filelist_path:
            return

        for key, value in data.items():
            # 检查文件路径
            if key in files:
                continue
            raise FileNotFoundError(f"Not found jinja2 file or directory for '{self.filelist_path}': '{key}'")

    def load_filelist(self) -> dict:
        """加载filelist yaml文件"""
        src = self.filelist_path
        variable = self.input_data

        if src:
            try:
                data = YAML.load(src, variable)
            except:
                print(f"failed to load filelist: {src}")
                raise
        else:
            data = {}

        # 要求输入字典
        if not isinstance(data, dict):
            raise Exception(f"The type of filelist should be a dictionary, but it is actually {type(data)}.")

        # 替换
        for key, value in data.items():
            # 支持表达式
            if isinstance(value, str):
                try:
                    value = eval(value)
                except:
                    pass

            # 要求值为布尔值
            if not isinstance(value, bool):
                raise Exception(f"The value '{value}' corresponding to the key '{key}' in filelist should be of type bool, but it is actually {type(value)}.")

            # 覆盖
            data[key] = value

        return data

    def manage_dirs(self, data: dict, templates: List[str], dirs: List[str]) -> List[str]:
        """
        管理目录。当目录无效时，下面所有文件均失效
        """
        f_is_inside = lambda x: any([dir for dir in invalid_dirs if Path(x).is_relative_to(dir)])

        invalid_dirs = [dir for dir in dirs if dir in data and not data[dir]]
        valid_templates = [x for x in templates if not f_is_inside(x)]
        return valid_templates

    def manage_files(self, data: dict, templates: List[str]) -> List[str]:
        """
        管理yaml文件
        """
        # 选取结果为真的
        files = [path for path in templates if path not in data or data[path]]
        return files
