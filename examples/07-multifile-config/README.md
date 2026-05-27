# 07 · 多文件配置（捆绑与 include）

输入支持两种多文件方式：

1. **单文件捆绑**：首行起用 `#文件名` 分段（如 `#a.yaml`），每段内容当作独立虚拟文件；入口为**第一段**。
2. **磁盘多文件**：在 YAML 中用 `!include` 引用同目录或其它相对路径文件；同一 mapping 下多行 `!include` 会深合并。

本示范 `config.bundle.yaml` 把 `a.yaml`、`spec.yaml`、`b.json`、`c.yaml` 写进一个文件；`${vars.nodes}` 在解析后展开。

## 生成

```bat
example.bat 07-multifile-config
```

查看 `generated/summary`。

## 回到总览

[examples/README.md](../README.md)
