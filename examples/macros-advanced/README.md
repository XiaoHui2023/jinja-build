# 宏与模板继承

## macro 定义与调用

```jinja
{% macro field_row(label, value) -%}
{{ label }}: {{ value }}
{%- endmacro %}

{{ field_row('name', name) }}
```

宏像可复用的模板函数；`-` 控制宏标签旁空白。

## 从文件导入宏

```jinja
{% from '_macros.j2' import field_row, callout with context %}
{% import '_macros.j2' as m %}
{{ m.field_row('x', 1) }}
```

`from` 导入单个宏；`import … as` 得到命名空间。`with context` 让宏内能访问外层模板变量。

## extends 与 block

```jinja
{% extends 'layout.j2' %}
{% block doc %}
正文
{% endblock %}
```

子模板填充基模板的 `{% block %}` 区域。

## call 块

```jinja
{% call callout('提示') %}
多行正文
{% endcall %}
```

宏内通过 `{{ caller() }}` 插入 call 块内容（见 `_macros.j2`）。
