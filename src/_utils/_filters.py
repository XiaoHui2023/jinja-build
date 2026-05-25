import inspect
from collections.abc import Callable
from typing import Any


def bind_instance_method_filter(method: Callable[..., object], instance: object) -> Callable[..., object]:
    """把实例方法绑成 Jinja 过滤器（管道左侧值可忽略）。"""

    def filter_impl(_value: object, *args: object, **kwargs: object) -> object:
        return method(instance, *args, **kwargs)

    return filter_impl


def build_model_method_filters(models_type: type, instance: object) -> dict[str, Callable[..., object]]:
    """从主数据类收集可在模板里用管道语法调用的实例方法。"""
    filters: dict[str, Callable[..., object]] = {}
    for name, member in vars(models_type).items():
        if name.startswith("_") or not inspect.isfunction(member):
            continue
        filters[name] = bind_instance_method_filter(member, instance)
    return filters


def _replace_filter(value: object, old: str, new: str, count: int = -1) -> str:
    text = str(value)
    if count < 0:
        return text.replace(old, new)
    return text.replace(old, new, count)


def _format_filter(value: object, *args: object, **kwargs: object) -> str:
    return str(value).format(*args, **kwargs)


def _strip_filter(value: object, chars: str | None = None) -> str:
    text = str(value)
    return text.strip(chars) if chars is not None else text.strip()


_BUILTIN_FILTER_BUILDERS: dict[str, Callable[..., object]] = {
    "abs": abs,
    "bool": bool,
    "float": float,
    "int": int,
    "len": len,
    "list": list,
    "repr": repr,
    "round": round,
    "str": str,
    "tuple": tuple,
    "set": set,
    "upper": lambda value: str(value).upper(),
    "lower": lambda value: str(value).lower(),
    "strip": _strip_filter,
    "replace": _replace_filter,
    "format": _format_filter,
    "startswith": lambda value, prefix: str(value).startswith(prefix),
    "endswith": lambda value, suffix: str(value).endswith(suffix),
    "split": lambda value, sep=None, maxsplit=-1: str(value).split(sep, maxsplit),
    "join": lambda value, iterable: str(value).join(iterable),
    "zfill": lambda value, width: str(value).zfill(width),
}


def build_builtin_filters() -> dict[str, Callable[..., object]]:
    """常用内置与字符串处理函数，供模板管道语法使用。"""
    return dict(_BUILTIN_FILTER_BUILDERS)


__all__ = [
    "bind_instance_method_filter",
    "build_builtin_filters",
    "build_model_method_filters",
]
