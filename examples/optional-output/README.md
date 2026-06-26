# 可选输出文件

渲染结果去掉首尾空白后若为空，**不创建**该输出文件。

## 配置开关

```yaml
emit_readme: true
emit_extra: false
```

布尔字段控制是否生成某类产物。

## 模板包一层 if

```jinja
{% if emit_readme %}
# {{ title }}
正文
{% endif %}
```

`emit_readme` 为 `false` 时分支无输出，对应文件不会出现。

## 避免空白占位

```jinja
{% if emit_extra %}extra: {{ name }}{% endif %}
```

关闭开关时不要留仅含空格或换行的内容，否则仍可能写盘。
