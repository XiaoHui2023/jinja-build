import re
import sys
import inspect
from pathlib import Path
from typing import Dict, Callable, Type, Any, List, Optional
from jinja2 import Environment, StrictUndefined, FileSystemLoader
from pydantic import BaseModel
from .dynamic_loading import load_module
from dataclasses import is_dataclass, asdict, field


def render(src: str, data: Any, globals_var: Dict[str, Any] = None, search_paths: List[str] = None) -> str:
    """
    渲染jinja

    src: jinja2模板文件
    data: 输入实例
    globals_var: 类名 - 类实体, 公用函数
    """
    if globals_var is None:
        globals_var = {}

    if search_paths is None:
        search_paths = []

    # read
    with open(src, "r", encoding="utf-8") as f:
        content = f.read()

    env = get_env(src, search_paths, globals_var)
    try:
        tp = env.from_string(content)
    except Exception as e:
        print(EXCEPTION.format(
            class_name=e.__class__.__name__,
            message=e.message,
            file=src,
            line=e.lineno,
            info=e.source.splitlines()[e.lineno - 1],
        ))
        raise

    # 转换
    data = to_dict(data)

    # 渲染模板
    try:
        output = tp.render(data)
    except:
        print(f"failed to render '{src}'")
        raise

    return output


def get_env(file_path: str, search_paths: List[str], globals_var: Dict[str, Any]) -> Environment:
    """
    获取渲染环境
    """
    current_dir = Path(file_path).parent

    env = SafeDictEnvironment(
        undefined=StrictUndefined,
        loader=FileSystemLoader(search_paths + [current_dir]),
        lstrip_blocks=True,
        extensions=[
            'jinja2.ext.do',
            'jinja2.ext.loopcontrols',
        ],
    )

    var_map = BASE_GLOBALS | globals_var
    env.globals.update({name: f for name, f in var_map.items()})

    for name, f in var_map.items():
        if not name:
            name = f.__name__
        env.filters[name] = f

    return env


def load_filter(file_path: str) -> List[Callable]:
    """从过滤器文件

    file_path : 文件路径

    returns:
        过滤函数列表
    """
    attrs = load_module(str(file_path))
    func_map = {name: x for name, x in attrs.items() if inspect.isfunction(x)}

    if len(func_map) == 0:
        raise Exception(f"Not found function in '{file_path}'")

    funcs = list(func_map.values())

    return funcs


def load_models(file_path: str) -> List[Type]:
    """从模型文件

    file_path : 文件路径

    returns:
        数据模型类列表
    """
    attrs = load_module(str(file_path))
    cls_map = {name: x for name, x in attrs.items() if inspect.isclass(x)}

    if len(cls_map) == 0:
        raise Exception(f"Not found class in '{file_path}'")

    cls = list(cls_map.values())

    return cls


def to_dict(data: object) -> Any:
    """递归转换对象为字典
    If isinstance(data, object) and data.__class__.__module__ != "builtins"
        rt = {k: getattr(data, k) for k in dir(data) if not k.startswith("_")}
    else:
        rt = data
    """
    if isinstance(data, BaseModel):
        rt = data.model_dump(by_alias=True)
        return rt


def to_dict(data: Any) -> Any:
    """递归转换 dict、list、dataclass / BaseModel / 基础对象 / property"""
    # None 或基础对象直接返回
    if data is None or isinstance(data, (str, int, float, bool)):
        return data

    # list / tuple / set 递归处理
    if isinstance(data, (list, tuple, set)):
        return [to_dict(v) for v in data]

    # dict 递归处理
    if isinstance(data, dict):
        return {k: to_dict(v) for k, v in data.items()}

    # dataclass
    if is_dataclass(data):
        return {k: to_dict(v) for k, v in asdict(data).items()}

    # pydantic BaseModel
    if isinstance(data, BaseModel):
        return data.model_dump(by_alias=True)

    # 普通对象（包含 property）
    result = {}
    for attr_name in dir(data):
        # 跳过私有和魔法属性
        if attr_name.startswith("_"):
            continue
        try:
            attr_value = getattr(data, attr_name)
        except Exception:
            continue
        # 跳过方法
        if callable(attr_value):
            continue
        result[attr_name] = to_dict(attr_value)

    return result


class SafeDictEnvironment(Environment):
    def getattr(self, obj, attribute):
        # 如果是 dict 并且属性存在，优先返回键值
        if isinstance(obj, dict) and attribute in obj:
            return obj[attribute]
        # 否则使用默认逻辑
        return super().getattr(obj, attribute)


EXCEPTION = """
{class_name} - {message}
file: {file}
line: {line}
{info}
"""


BASE_GLOBALS = {
    'len': len,
}


__all__ = [
    'render',
    'load_filter',
]
