# 过滤器与 models.py

jinja-build 把三类能力交给模板：配置字段、`models.py` 的 property / 方法、内置管道过滤器。

## property 作变量

```python
@property
def label(self) -> str:
    return self.raw.upper()
```

```jinja
label={{ label }}
```

`@property` 在模板里当普通字段用，不写括号。

## 内置过滤器

```jinja
{{ raw | replace('l', 'L') }}
{{ raw | upper }}
{{ '-' | join(items) }}
{{ items | len }}
```

由工具注册，语法为 `值 | 过滤器(参数)`。

## models 方法作过滤器

```python
def title(self) -> str:
    return f"title:{self.raw}"

def wrap(self, prefix: str) -> str:
    return f"{prefix}{self.raw}{prefix}"
```

```jinja
title_filter: {{ '' | title }}
wrap: {{ raw | wrap('**') }}
```

主数据类上的公开实例方法同时注册为过滤器；管道左侧值通常忽略，参数传给方法。仍可用 `{{ title() }}` 函数写法。
