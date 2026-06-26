# Jinja 基础语法

本目录用多个小模板分别演示常见写法。配置字段来自 `config.yaml`，经 `models.py` 校验后可直接在模板里用字段名。

## 变量与表达式

```jinja
{{ title }}
{{ count + 1 }}
{{ note | default('（无）') }}
{{ items[0].name }}
```

`{{ }}` 输出表达式；`|` 接过滤器；列表、字典用下标访问。

## 注释

```jinja
{# 行注释 #}
{#
  块注释
#}
```

注释不出现在生成结果里。

## 分支

```jinja
{% if enabled %}
on
{% elif count > 0 %}
partial
{% else %}
off
{% endif %}
```

## 循环

```jinja
{% for item in items %}
{{ loop.index }}. {{ item.name }}
{% else %}
（空列表）
{% endfor %}

{% for item in items if item.active %}
{{ item.name }}
{% endfor %}
```

`loop.index`、`loop.first`、`loop.last` 描述迭代状态；`for … else` 在零次迭代时走 `else`。

## set 与过滤器

```jinja
{% set total = items | sum(attribute='qty') %}
{{ label | upper }}
{{ items | length }}
```

`{% set %}` 定义局部变量；管道把左侧值传给过滤器。

## 空白控制

```jinja
{%- for x in items -%}
{{ x }}
{%- endfor -%}
```

标签两侧的 `-` 去掉该侧换行与空格，避免多余空行。

## 测试与逻辑

```jinja
{% if count is divisibleby(2) %}even{% endif %}
{% if missing is defined %}{{ missing }}{% endif %}
{% if items is iterable %}ok{% endif %}
```

`is` 接 Jinja 内置测试；可用 `and` / `or` / `not`。

## include

```jinja
{% include '_snippet_header.j2' %}
```

把片段模板插入当前位置；路径相对模板搜索目录。

## do 扩展

```jinja
{% set ns = namespace(tags=[]) %}
{% for item in items %}
{% do ns.tags.append(item.name) %}
{% endfor %}
```

`{% do %}` 执行副作用（本工具已启用 `jinja2.ext.do`）。

## 转义字面量

```jinja
\{\{ not rendered \}\}
{% raw %}{{ literal }}{% endraw %}
```

需要输出 `{{ }}` 字样时用反斜杠或 `raw` 块。
