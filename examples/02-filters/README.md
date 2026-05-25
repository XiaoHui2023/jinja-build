# 02 · 过滤器与 models.py

说明 jinja-build 如何把**内置管道过滤器**、**models.py 里的方法**和 **property** 提供给模板。

## 生成

```bat
example.bat 02-filters
```

查看 `generated/demo`。

## 要点

| 能力 | 模板写法 | 定义位置 |
| --- | --- | --- |
| property | `{{ label }}` | `models.py` 里 `@property` |
| 内置过滤器 | `{{ raw \| replace('l','L') }}`、`{{ items \| len }}` | 工具内置，见 `src/_utils/_filters.py` |
| 类方法作过滤器 | `{{ '' \| title }}`、`{{ raw \| wrap('**') }}` | `models.py` 主类公开实例方法 |
| 函数写法（兼容） | `{{ title() }}` | 同上，同时注册为全局函数 |

管道左侧的值对「绑定实例的方法过滤器」通常可忽略（示例里用 `'' | title`）。

## 下一步

[03-macros-advanced](../03-macros-advanced/README.md)
