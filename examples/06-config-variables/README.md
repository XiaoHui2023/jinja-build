# 06 · 配置文件中的变量引用

输入配置支持 **configlib** 的 `${…}` 解析（YAML / JSON / TOML 等，视扩展名而定）。可在加载后、填入 `models.py` 之前完成字段拼接与引用。

## 生成

```bat
example.bat 06-config-variables
```

查看 `generated/summary`。

## 本示范 config.yaml 用法

| 写法 | 含义 |
| --- | --- |
| `${vars.prefix}` | 绝对路径：从根上的 `vars.prefix` 取值 |
| `${vars.version}` | 数字会按规则自动转成 int |
| `${paths.base}` | 引用同级已解析字段 |
| `${project_name}-build` | 字符串内嵌引用（见 `nested.label`） |

还支持（见 configlib 文档）：`${..key}` 相对引用、`${env:NAME}` 环境变量、`${env:NAME:默认值}`。

## 注意

- 变量在**配置文件**里展开，展开后的 dict 再传给 `Data(**data)`。
- 模板里使用的是**解析后的字段**（如 `{{ project_name }}`），不是直接在 `.j2` 里写 `${}`。

## 回到总览

[examples/README.md](../README.md)
