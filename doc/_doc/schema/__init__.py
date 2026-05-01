from ._dataclass import is_dataclass_model, to_schema as dataclass_to_schema
from ._pydantic import is_pydantic_model, to_schema as pydantic_to_schema
from ._types import ClassSchema, FieldSchema


def collect_schemas(objects: list[object]) -> list[ClassSchema]:
    """按源码顺序收集可文档化的数据结构。"""
    schemas = []
    for obj in objects:
        if is_pydantic_model(obj):
            schemas.append(pydantic_to_schema(obj))
        elif is_dataclass_model(obj):
            schemas.append(dataclass_to_schema(obj))
    return schemas


__all__ = [
    "ClassSchema",
    "FieldSchema",
    "collect_schemas",
]
