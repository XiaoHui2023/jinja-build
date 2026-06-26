# 多文件配置

## 单文件捆绑

```yaml
#a.yaml
title: alpha
vars:
  nodes: [a, b]

#b.json
{"nodes": {"b": {"name": 7}}}
```

首行起用 `#文件名` 分段，每段当作独立虚拟文件；**第一段**为入口配置。

## 磁盘上的 include

```yaml
common: !include shared.yaml
extra: !include fragments/extra.yaml
```

同一 mapping 下多行 `!include` 会深合并。

## 与变量引用组合

捆绑段或 include 文件里仍可用 `${vars.nodes}` 等，在解析阶段展开后再实例化 models。
