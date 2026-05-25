# 01 · Jinja 基础语法

用多个小模板各生成一份说明文件，覆盖日常模板里最常见的 Jinja2 写法。读法：先运行生成，再对照 `generated/` 与本节列表。

## 生成

在仓库根执行：

```bat
example.bat 01-jinja-basics
```

## 本示范包含的语法点

| 输出文件 | 内容 |
| --- | --- |
| `01_variables` | `{{ }}` 变量、算术、比较、`default`、下标 |
| `02_comments` | `{# #}` 行注释与块注释 |
| `03_conditions` | `if` / `elif` / `else` |
| `04_loops` | `for` / `else`（空列表）、`loop.*`、`for … if` 过滤 |
| `05_set_and_filters` | `{% set %}`、`|upper`、`|sum(attribute=…)`、`|length`、`|default` |
| `06_whitespace` | `{%- -%}` 去掉多余换行与空格 |
| `07_tests_and_logic` | `is divisibleby`、`is defined`、`is iterable`、布尔表达式 |
| `08_include` | `{% include %}` 复用 `_snippet_header.j2` |
| `09_do_extension` | `{% do %}`（本工具已启用 `jinja2.ext.do`）在循环里改列表 |
| `10_escape` | 输出字面 `{{ }}`、`{% raw %}…{% endraw %}` |
| `_snippet_header` | include 用片段（可能多生成一小文件，可忽略） |

## 数据从哪来

- `config.yaml` 提供字段，由 `models.py` 里的 `Data` 校验并实例化。
- 模板里直接用字段名（如 `{{ title }}`、`{% for item in items %}`）。

## 下一步

学会基础后阅读 [02-filters](../02-filters/README.md)，了解 jinja-build 提供的管道过滤器与 `models.py` 方法。
