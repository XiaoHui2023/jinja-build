# 03 · 宏与模板继承

演示 **macro**、**call**、**extends / block**、**import … as** 等进阶结构。

## 生成

```bat
example.bat 03-macros-advanced
```

## 输出说明

| 文件 | 说明 |
| --- | --- |
| `layout` | 基模板，仅定义 `{% block doc %}` |
| `page` | `extends layout`，`from _macros import …`，填充 block |
| `macro_call` | `import _macros as m`、本地 macro |
| `_macros` | 宏定义库（可能被单独渲染出一行，可忽略） |

## 语法清单

- `{% macro name(arg) %}…{% endmacro %}`
- `{% from 'x.j2' import macro_name %}`
- `{% import 'x.j2' as lib %}`
- `{% call caller_macro() %}…{% endcall %}`（宏内需 `{{ caller() }}` 时再用）
- `{% extends 'base.j2' %}` + `{% block name %}…{% endblock %}`

## 下一步

[04-optional-output](../04-optional-output/README.md)
