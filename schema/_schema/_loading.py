import ast
import hashlib
import importlib.util
import sys
from pathlib import Path


def load_ordered_objects(file_path: str | Path) -> list[object]:
    """加载 Python 文件，并按源码顺序返回顶层定义。"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(path)

    abs_path = path.resolve()
    module = _load_module(abs_path)
    return [
        getattr(module, name)
        for name in _definition_names(abs_path)
        if hasattr(module, name)
    ]


def _load_module(file_path: Path) -> object:
    """用隔离名字加载单个数据结构文件。"""
    module_name = _module_name(file_path)
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {file_path}")

    module = importlib.util.module_from_spec(spec)
    old_path = sys.path.copy()
    sys.modules[module_name] = module
    try:
        sys.path.insert(0, str(file_path.parent))
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    finally:
        sys.path[:] = old_path
    return module


def _definition_names(file_path: Path) -> list[str]:
    """读取源码里顶层类和函数的定义顺序。"""
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source, str(file_path))
    names = []
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            names.append(node.name)
    return names


def _module_name(file_path: Path) -> str:
    """根据绝对路径生成私有模块名。"""
    digest = hashlib.sha256(str(file_path).encode("utf-8")).hexdigest()[:16]
    return f"_jinja_build_schema_{file_path.stem}_{digest}"
