# models.py

每个模板目录需要一个数据结构文件，默认文件名为 `models.py`。jinja-build 按源码中的顶层定义顺序加载对象，并使用最后一个顶层类实例化输入配置。

推荐把最后一个类命名为 `Models`。普通类、dataclass、Pydantic 都可以使用；Pydantic 最适合写有校验、有默认值、有嵌套结构的模板数据。

## 项目结构

```text
templates/
  models.py          # 数据结构与模板辅助方法
  summary.md.j2      # 模板文件，输出为 summary.md
  include/
    part.j2          # 可被其它模板 include
```

会递归渲染目录内所有 `*.j2` 文件，并保留相对路径。

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

模板中可以直接读取字段和 property：

```jinja
# {{ title }}
{% for item in active_items %}
- {{ item.name }}: {{ item.qty }}
{% endfor %}
```

公开实例方法会同时作为全局函数和过滤器暴露：

```jinja
{{ upper_title() }}
{{ "" | upper_title }}
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

dataclass 适合轻量配置，但嵌套对象通常需要自己处理类型转换。输入配置中的 dict 不会自动变成嵌套 dataclass，除非你在构造逻辑里显式转换。

## 普通类写法

```python
class Models:
    def __init__(self, title: str = "demo", items: list[dict] | None = None):
        self.title = title
        self.items = items or []

    @property
    def count(self) -> int:
        return len(self.items)
```

普通类适合非常小的模板。需要默认值、类型转换、嵌套校验时，改用 Pydantic。

## 导入与辅助文件

`models.py` 加载时，所在目录会临时加入 `sys.path`。同一模板目录下可以放辅助模块：

```text
templates/
  models.py
  demo_lib/
    __init__.py
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

不同模板目录里的同名 `models.py` 会用私有模块名隔离加载，避免批量运行时互相污染。

## 可选文件

渲染结果去掉首尾空白后为空时，不会创建输出文件，也不会为它创建空目录。

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

这种方式适合可选 README、可选声明、可选配置片段。关闭时模板不要输出占位空格。
