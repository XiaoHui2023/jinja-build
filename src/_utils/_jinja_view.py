from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any

from jinja2 import StrictUndefined
from pydantic import BaseModel

from ._jinja_convert import _property_values, read_property_value

_PRIMITIVE_TYPES = (str, int, float, bool, type(None))


def _is_primitive(value: Any) -> bool:
    return isinstance(value, _PRIMITIVE_TYPES)


def _source_label(value: Any) -> str:
    if value is None:
        return "None"
    return type(value).__qualname__


def _field_aliases(field_info: object) -> tuple[str, ...]:
    names: list[str] = []
    for key in ("alias", "serialization_alias"):
        alias = getattr(field_info, key, None)
        if alias and alias not in names:
            names.append(alias)
    return tuple(names)


def _resolve_property(obj: object, name: str) -> tuple[Any, bool]:
    descriptor = getattr(type(obj), name, None)
    if not isinstance(descriptor, property):
        return None, False
    return getattr(obj, name), True


def _resolve_pydantic(obj: BaseModel, name: str) -> tuple[Any, bool]:
    model_fields = type(obj).model_fields
    if name in model_fields:
        return getattr(obj, name), True

    for field_name, field_info in model_fields.items():
        if name in _field_aliases(field_info):
            return getattr(obj, field_name), True

    computed = getattr(type(obj), "model_computed_fields", None)
    if isinstance(computed, dict) and name in computed:
        return getattr(obj, name), True

    resolved = _resolve_property(obj, name)
    if resolved[1]:
        return resolved

    try:
        value = getattr(obj, name)
    except AttributeError:
        return None, False
    if name.startswith("_") or callable(value):
        return None, False
    return value, True


def _resolve_dataclass(obj: object, name: str) -> tuple[Any, bool]:
    if name in {field.name for field in fields(obj)}:
        return getattr(obj, name), True

    resolved = _resolve_property(obj, name)
    if resolved[1]:
        return resolved

    try:
        value = getattr(obj, name)
    except AttributeError:
        return None, False
    if name.startswith("_") or callable(value):
        return None, False
    return value, True


def resolve_attribute(obj: object, name: str) -> tuple[Any, bool]:
    """按模板约定顺序解析属性名。"""
    if isinstance(obj, BaseModel):
        return _resolve_pydantic(obj, name)

    if is_dataclass(obj):
        return _resolve_dataclass(obj, name)

    if isinstance(obj, dict):
        if name in obj:
            return obj[name], True
        return None, False

    resolved = _resolve_property(obj, name)
    if resolved[1]:
        return resolved

    try:
        value = getattr(obj, name)
    except AttributeError:
        return None, False
    if name.startswith("_") or callable(value):
        return None, False
    return value, True


def wrap_value(value: Any, *, path: str, source_type: str | None = None) -> Any:
    """把嵌套值包成模板视图；标量原样返回。"""
    if _is_primitive(value):
        return value

    if isinstance(value, (list, tuple)):
        label = source_type or _source_label(value)
        wrapped = [
            wrap_value(item, path=f"{path}[{index}]", source_type=_source_label(item))
            for index, item in enumerate(value)
        ]
        return type(value)(wrapped)

    label = source_type or _source_label(value)
    return TemplateView(value, path=path, source_type=label)


def _pydantic_context_key(field_info: object, field_name: str) -> str:
    serialization_alias = getattr(field_info, "serialization_alias", None)
    if serialization_alias:
        return serialization_alias
    alias = getattr(field_info, "alias", None)
    if alias:
        return alias
    return field_name


def _context_entries(data: object) -> dict[str, Any]:
    """列出根对象在模板顶层可用的名字与原始值。"""
    if isinstance(data, BaseModel):
        entries: dict[str, Any] = {}
        for field_name, field_info in type(data).model_fields.items():
            key = _pydantic_context_key(field_info, field_name)
            entries[key] = getattr(data, field_name)
        for name, value in _property_values(data).items():
            if name not in entries:
                entries[name] = value
        return entries

    if is_dataclass(data):
        entries = {field.name: getattr(data, field.name) for field in fields(data)}
        for name, value in _property_values(data).items():
            if name not in entries:
                entries[name] = value
        return entries

    if isinstance(data, dict):
        return dict(data)

    entries: dict[str, Any] = {}
    for name in dir(data):
        if name.startswith("_"):
            continue
        descriptor = getattr(type(data), name, None)
        if isinstance(descriptor, property):
            value = read_property_value(data, name)
        else:
            try:
                value = getattr(data, name)
            except Exception:
                continue
        if callable(value):
            continue
        entries[name] = value
    return entries


def build_render_context(data: Any) -> dict[str, Any]:
    """把输入对象展开为 Jinja 顶层上下文，嵌套值用 TemplateView 包裹。"""
    if _is_primitive(data):
        return {"": data}

    return {
        name: wrap_value(value, path=name, source_type=_source_label(value))
        for name, value in _context_entries(data).items()
    }


def wrap_for_template(data: Any) -> Any:
    """把单个值包成模板视图（供嵌套访问或测试使用）。"""
    return wrap_value(data, path="root", source_type=_source_label(data))


class TemplateView:
    """模板访问代理：保留原始类型，按字段名、alias、property 等解析。"""

    __slots__ = ("_obj", "_path", "_source_type")

    def __init__(self, obj: object, *, path: str, source_type: str | None = None) -> None:
        self._obj = obj
        self._path = path
        self._source_type = source_type or type(obj).__qualname__

    @property
    def source_type_name(self) -> str:
        return self._source_type

    @property
    def template_path(self) -> str:
        return self._path

    def get_attribute(self, name: str) -> Any:
        value, found = resolve_attribute(self._obj, name)
        if not found:
            raise AttributeError(name)
        return wrap_value(value, path=f"{self._path}.{name}", source_type=_source_label(value))

    def get_item(self, key: Any) -> Any:
        try:
            value = self._obj[key]
        except (KeyError, IndexError, TypeError) as exc:
            raise KeyError(key) from exc
        key_label = repr(key)
        return wrap_value(
            value,
            path=f"{self._path}[{key_label}]",
            source_type=_source_label(value),
        )

    def __iter__(self) -> Any:
        obj = self._obj
        if isinstance(obj, dict):
            return iter(obj)
        if isinstance(obj, (list, tuple)):
            return iter(
                wrap_value(
                    item,
                    path=f"{self._path}[{index}]",
                    source_type=_source_label(item),
                )
                for index, item in enumerate(obj)
            )
        raise TypeError(f"{self._source_type} 不支持在模板中直接迭代")


class TemplateStrictUndefined(StrictUndefined):
    """未定义变量报错时带上模板视图记录的类型名。"""

    @property
    def _undefined_message(self) -> str:
        obj = self._undefined_obj
        name = self._undefined_name
        if isinstance(obj, TemplateView) and isinstance(name, str):
            return f'{obj.source_type_name} 缺少模板字段 "{name}"'
        return super()._undefined_message


__all__ = [
    "TemplateStrictUndefined",
    "TemplateView",
    "build_render_context",
    "resolve_attribute",
    "wrap_for_template",
    "wrap_value",
]
