# 04 · 用开关控制是否生成文件

结合配置字段与 `{% if %}`，控制某个模板是否产出文件。jinja-build 规则：**渲染结果去掉首尾空白后若为空，则不创建该输出文件**（也不会为它建空目录）。

## 生成

```bat
example.bat 04-optional-output
```

默认 `config.yaml` 中 `emit_readme: true`、`emit_extra: false`。

## 预期产物

| 模板 | 是否生成 | 原因 |
| --- | --- | --- |
| `always.j2` | 是 | 始终有内容 |
| `optional_readme.j2` | 是 | `emit_readme` 为 true |
| `optional_extra.j2` | 否 | `emit_extra` 为 false，分支无输出 |
| `optional_whitespace_only.j2` | 否 | 仅空白 |

修改 `config.yaml` 把 `emit_extra` 改为 `true` 后重新生成，可看到 `optional_extra` 出现。

## 推荐写法

1. 在配置里放布尔开关（如 `emit_xxx`）。
2. 模板顶层用 `{% if emit_xxx %}…{% endif %}` 包住全部正文。
3. 关闭时不要输出空格或换行占位。

## 下一步

[05-models-imports](../05-models-imports/README.md)
