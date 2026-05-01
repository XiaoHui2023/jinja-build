from pydantic import BaseModel

from ._format import format_default, format_type
from ._types import ClassSchema, FieldSchema


def is_pydantic_model(obj: object) -> bool:
    """判断对象是不是 Pydantic 数据模型。"""
    return isinstance(obj, type) and issubclass(obj, BaseModel)


def to_schema(model_type: type[BaseModel]) -> ClassSchema:
    """把 Pydantic 模型转成统一结构。"""
    fields = []
    for name, info in model_type.model_fields.items():
        default = None
        if not info.is_required():
            if info.default_factory is not None:
                default = "<factory>"
            else:
                default = format_default(info.default)
        fields.append(
            FieldSchema(
                name=info.alias or name,
                type=format_type(info.annotation),
                required=info.is_required(),
                default=default,
                description=info.description,
            )
        )

    return ClassSchema(
        name=model_type.__name__,
        kind="Pydantic",
        description=model_type.__doc__,
        fields=fields,
    )
