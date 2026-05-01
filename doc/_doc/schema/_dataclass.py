import ast
import dataclasses
import inspect
from dataclasses import MISSING

from ._format import format_default, format_type
from ._types import ClassSchema, FieldSchema


def is_dataclass_model(obj: object) -> bool:
    """判断对象是不是 dataclass 类型。"""
    return isinstance(obj, type) and dataclasses.is_dataclass(obj)


def to_schema(model_type: type) -> ClassSchema:
    """把 dataclass 类型转成统一结构。"""
    fields = []
    docstrings = _field_docstrings(model_type)
    for item in dataclasses.fields(model_type):
        required = item.default is MISSING and item.default_factory is MISSING
        default = None
        if not required:
            if item.default_factory is not MISSING:
                default = "<factory>"
            else:
                default = format_default(item.default)
        description = _field_description(item) or docstrings.get(item.name)
        fields.append(
            FieldSchema(
                name=item.name,
                type=format_type(item.type),
                required=required,
                default=default,
                description=description,
            )
        )

    return ClassSchema(
        name=model_type.__name__,
        kind="dataclass",
        description=model_type.__doc__,
        fields=fields,
    )


def _field_description(item: dataclasses.Field) -> str | None:
    """读取字段元信息里的说明。"""
    value = item.metadata.get("description")
    if isinstance(value, str) and value.strip():
        return value
    return None


def _field_docstrings(model_type: type) -> dict[str, str]:
    """读取字段下一行的独立说明字符串。"""
    try:
        source = inspect.getsource(model_type)
    except OSError:
        return {}

    tree = ast.parse(source)
    class_node = next((node for node in tree.body if isinstance(node, ast.ClassDef)), None)
    if class_node is None:
        return {}

    docs = {}
    body = class_node.body
    for index, node in enumerate(body[:-1]):
        if not isinstance(node, ast.AnnAssign) or not isinstance(node.target, ast.Name):
            continue
        next_node = body[index + 1]
        if (
            isinstance(next_node, ast.Expr)
            and isinstance(next_node.value, ast.Constant)
            and isinstance(next_node.value.value, str)
        ):
            docs[node.target.id] = next_node.value.value.strip()
    return docs
