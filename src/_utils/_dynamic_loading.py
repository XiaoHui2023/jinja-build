import ast
import hashlib
import importlib.util
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any


@contextmanager
def models_import_path(file_path: str | Path) -> Iterator[Path]:
    """在上下文期间把 models.py 父目录留在 sys.path，供延迟导入使用。

    Args:
        file_path: models.py 或其它数据结构文件路径
    """
    parent = Path(file_path).resolve().parent
    parent_text = str(parent)
    inserted = False
    if parent_text not in sys.path:
        sys.path.insert(0, parent_text)
        inserted = True
    try:
        yield parent
    finally:
        if inserted:
            try:
                sys.path.remove(parent_text)
            except ValueError:
                pass


def load_module(file_path: str | Path) -> dict[str, Any]:
    """载入指定文件并按源码定义顺序返回可用对象。

    Args:
        file_path: 要载入的文件路径
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(path)

    abs_path = path.resolve()
    module_name = _module_name(abs_path)
    sys_path = sys.path.copy()
    try:
        sys.path.insert(0, str(abs_path.parent))
        module = _load_module_from_path(module_name, abs_path)
    finally:
        sys.path[:] = sys_path

    return {
        name: getattr(module, name)
        for name in get_definitions_in_order(abs_path)
    }


def _load_module_from_path(module_name: str, file_path: Path) -> object:
    """用私有模块名加载单个 Python 文件。"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


def _module_name(file_path: Path) -> str:
    """根据绝对路径生成不会和普通模块重名的私有名字。"""
    digest = hashlib.sha256(str(file_path).encode("utf-8")).hexdigest()[:16]
    return f"_jinja_build_dynamic_{file_path.stem}_{digest}"


def get_definitions_in_order(filename: str | Path) -> list[str]:
    """按源码顺序读取顶层定义名。

    Args:
        filename: 要解析的源码文件
    """
    with open(filename, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source, str(filename))
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
    "get_definitions_in_order",
    "load_module",
    "models_import_path",
]
