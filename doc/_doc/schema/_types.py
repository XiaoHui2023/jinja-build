from dataclasses import dataclass, field


@dataclass(frozen=True)
class FieldSchema:
    """描述一个模型字段，供 Markdown 生成器读取。"""

    name: str
    """字段展示名"""
    type: str
    """字段取值类型"""
    required: bool
    """调用方是否必须填写"""
    default: str | None = None
    """字段默认值，缺省时没有展示值"""
    description: str | None = None
    """给读者看的字段说明"""


@dataclass(frozen=True)
class ClassSchema:
    """描述一个数据结构类，统一承接不同建模库的结果。"""

    name: str
    """类型名称"""
    kind: str
    """类型来源，例如 Pydantic 或 dataclass"""
    description: str | None = None
    """类型自己的说明文字"""
    fields: list[FieldSchema] = field(default_factory=list)
    """类型里的字段列表"""
