# models.py

每个模板目录需要一个数据结构文件，默认文件名为 `models.py`。

- 以最后一个类作为数据结构入口
- 递归渲染目录内所有 `*.j2` 文件

## Pydantic 写法

```python
from pydantic import BaseModel


class Item(BaseModel):
    name: str
    qty: int
    active: bool = True


class Models(BaseModel):
    title: str
    items: list[Item]
    note: str | None = None

    @property
    def active_items(self) -> list[Item]:
        return [item for item in self.items if item.active]

    def upper_title(self) -> str:
        return self.title.upper()
```

## dataclass 写法

```python
from dataclasses import dataclass, field


@dataclass
class Item:
    name: str
    qty: int


@dataclass
class Models:
    title: str
    items: list[Item] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.items)
```

## 普通类写法

```python
class Item:
    def __init__(self, name: str, qty: int):
        self.name = name
        self.qty = qty


class Models:
    def __init__(self, title: str = "demo", items: list[Item] | None = None):
        self.title = title
        self.items = items or []

    @property
    def count(self) -> int:
        return len(self.items)
```

## 过滤器

支持以下过滤器：

- models中的普通函数
- models中的property函数
- jinja内置过滤器
- python内置函数

## 导入子脚本

使用绝对路径导入：

```text
templates/
  models.py
  demo_lib/
    formats.py
```

```python
from pydantic import BaseModel

from demo_lib.formats import slugify


class Models(BaseModel):
    name: str

    def slug(self) -> str:
        return slugify(self.name)
```

`models.py` 同目录下的模块可在加载时导入，也可在 `@property` 或方法内延迟导入；整次构建期间该目录保持在 Python 搜索路径中。

## 可选文件

渲染结果为空时，不会创建输出文件，也不会为它创建空目录。

```jinja
{% if emit_extra %}
extra: {{ name }}
{% endif %}
```

配置中用布尔变量控制：

```yaml
name: demo
emit_extra: false
```
