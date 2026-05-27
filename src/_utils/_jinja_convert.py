import inspect
from dataclasses import asdict, is_dataclass
from typing import Any

from pydantic import BaseModel


def _property_values(data: object) -> dict[str, object]:
    """读取实例上由 property 提供的字段。"""
    values: dict[str, object] = {}
    for name in dir(data):
        if name.startswith("_"):
            continue
        descriptor = getattr(type(data), name, None)
        if not isinstance(descriptor, property):
            continue
        try:
            values[name] = getattr(data, name)
        except Exception:
            continue
    return values


def _merge_properties(base: dict[str, Any], data: object) -> dict[str, Any]:
    """把 property 值并入字典，不覆盖已有键。"""
    for name, value in _property_values(data).items():
        if name not in base:
            base[name] = to_dict(value)
    return base


def to_dict(data: Any) -> Any:
    """把输入对象递归转成模板更容易读取的结构。"""
    if data is None or isinstance(data, (str, int, float, bool)):
        return data

    if isinstance(data, (list, tuple, set)):
        return [to_dict(v) for v in data]

    if isinstance(data, dict):
        return {k: to_dict(v) for k, v in data.items()}

    if is_dataclass(data):
        return _merge_properties({k: to_dict(v) for k, v in asdict(data).items()}, data)

    if isinstance(data, BaseModel):
        return _merge_properties(dict(data.model_dump(by_alias=True)), data)

    result: dict[str, Any] = {}
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


__all__ = [
    "to_dict",
]
