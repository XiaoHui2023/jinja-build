import os
import sys
import ast
from typing import List, Dict, Any
import importlib.util
from enum import Enum, auto
from types import FunctionType
from collections.abc import Mapping


def load_module(file_path: str) -> Dict[str, Any]:
    """
    载入指定文件

    Returns:
        属性名字: 值 映射表
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)

    # 解析模块的路径
    abs_path = os.path.abspath(file_path)
    dir_path = os.path.dirname(abs_path)
    pkg_path = os.path.basename(dir_path)
    module_path = os.path.splitext(os.path.basename(file_path))[0]

    # 阻止重复导入 sys.path，确保临时可访问
    sys.path.insert(0, dir_path)

    # 构建spec
    spec = importlib.util.spec_from_file_location(module_path, file_path)

    # 创建模块
    my_module = importlib.util.module_from_spec(spec)

    # 执行模块
    spec.loader.exec_module(my_module)

    # 得到定义顺序
    names_ordered = get_definitions_in_order(file_path)

    # 获得属性并过滤
    attrs = {name: getattr(my_module, name) for name in names_ordered}

    return attrs


def get_definitions_in_order(filename: str) -> List[str]:
    """
    解析源代码定义顺序
    """
    with open(filename, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source, filename)

    names_in_order = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            names_in_order.append(node.name)
        elif isinstance(node, ast.ClassDef):
            names_in_order.append(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names_in_order.append(target.id)
    return names_in_order


__all__ = [
    "load_module",
]
