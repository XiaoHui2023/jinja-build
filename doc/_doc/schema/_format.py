import types
from collections.abc import Callable
from typing import Any, get_args, get_origin


def format_type(annotation: object) -> str:
    """把类型注解转成文档里容易扫读的短文本。"""
    if annotation is None:
        return "None"
    if annotation is Any:
        return "Any"
    if annotation is inspect_empty():
        return "未知"

    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin in (types.UnionType, None) and isinstance(annotation, types.UnionType):
        return " | ".join(format_type(arg) for arg in args)
    if origin is None:
        return getattr(annotation, "__name__", str(annotation).replace("typing.", ""))
    if origin is Callable:
        return "callable"
    if origin is list:
        return _format_generic("list", args)
    if origin is dict:
        return _format_generic("dict", args)
    if origin is tuple:
        return _format_generic("tuple", args)
    if origin is set:
        return _format_generic("set", args)
    if str(origin) == "typing.Union":
        return " | ".join(format_type(arg) for arg in args)
    return _format_generic(getattr(origin, "__name__", str(origin).replace("typing.", "")), args)


def format_default(value: object) -> str:
    """把默认值压成一行，避免表格被长对象撑开。"""
    text = repr(value)
    if len(text) > 60:
        return text[:57] + "..."
    return text


def inspect_empty() -> object:
    """返回标准库用于表示缺省注解的占位值。"""
    import inspect

    return inspect.Signature.empty


def _format_generic(name: str, args: tuple[object, ...]) -> str:
    """渲染带参数的容器类型。"""
    if not args:
        return name
    return f"{name}[{', '.join(format_type(arg) for arg in args)}]"
