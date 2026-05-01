import inspect
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from pydantic import BaseModel

from ._dynamic_loading import load_module


def render(
    src: str | Path,
    data: Any,
    globals_var: dict[str, object] | None = None,
    search_paths: list[str | Path] | None = None,
) -> str:
    """渲染模板文件。

    Args:
        src: 模板文件路径
        data: 输入数据对象
        globals_var: 模板里可直接调用的对象
        search_paths: 模板继承和包含时可搜索的目录
    """
    if globals_var is None:
        globals_var = {}

    if search_paths is None:
        search_paths = []

    with open(src, "r", encoding="utf-8") as f:
        content = f.read()

    env = get_env(src, search_paths, globals_var)
    try:
        template = env.from_string(content)
    except Exception as e:
        print(EXCEPTION.format(
            class_name=e.__class__.__name__,
            message=e.message,
            file=src,
            line=e.lineno,
            info=e.source.splitlines()[e.lineno - 1],
        ))
        raise

    data = to_dict(data)
    try:
        output = template.render(data)
    except:
        print(f"failed to render '{src}'")
        raise

    return output


def get_env(file_path: str | Path, search_paths: list[str | Path], globals_var: dict[str, object]) -> Environment:
    """创建单个模板文件使用的渲染环境。"""
    current_dir = Path(file_path).parent

    env = SafeDictEnvironment(
        undefined=StrictUndefined,
        loader=FileSystemLoader(search_paths + [current_dir]),
        lstrip_blocks=True,
        extensions=[
            "jinja2.ext.do",
            "jinja2.ext.loopcontrols",
        ],
    )

    var_map = BASE_GLOBALS | globals_var
    env.globals.update({name: f for name, f in var_map.items()})

    return env


def load_models(file_path: str | Path) -> list[type]:
    """从数据结构文件读取可用类型。

    Args:
        file_path: 数据结构文件路径
    """
    attrs = load_module(file_path)
    cls_map = {name: x for name, x in attrs.items() if inspect.isclass(x)}

    if len(cls_map) == 0:
        raise Exception(f"Not found class in '{file_path}'")

    return list(cls_map.values())


def to_dict(data: Any) -> Any:
    """把输入对象递归转成模板更容易读取的结构。"""
    if data is None or isinstance(data, (str, int, float, bool)):
        return data

    if isinstance(data, (list, tuple, set)):
        return [to_dict(v) for v in data]

    if isinstance(data, dict):
        return {k: to_dict(v) for k, v in data.items()}

    if is_dataclass(data):
        return {k: to_dict(v) for k, v in asdict(data).items()}

    if isinstance(data, BaseModel):
        return data.model_dump(by_alias=True)

    result = {}
    for attr_name in dir(data):
        if attr_name.startswith("_"):
            continue
        try:
            attr_value = getattr(data, attr_name)
        except Exception:
            continue
        if callable(attr_value):
            continue
        result[attr_name] = to_dict(attr_value)

    return result


class SafeDictEnvironment(Environment):
    """让模板读取字典时优先按键名取值。"""

    def getattr(self, obj: object, attribute: str) -> object:
        """读取模板里的属性访问。"""
        if isinstance(obj, dict) and attribute in obj:
            return obj[attribute]
        return super().getattr(obj, attribute)


EXCEPTION = """
{class_name} - {message}
file: {file}
line: {line}
{info}
"""


BASE_GLOBALS = {
    "len": len,
}


__all__ = [
    "load_models",
    "render",
]
