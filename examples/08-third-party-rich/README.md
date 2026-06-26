# 08 · models.py 使用第三方库 rich

演示在 `models.py` 中导入 **已安装** 的第三方库（`rich`），并在模板里调用方法生成输出。也用于验证 PyInstaller 单文件是否完整打包 `rich` 子模块。

## 生成

```bat
example.bat 08-third-party-rich
```

用打包后的可执行文件：

```bat
dist\jinja-build.exe -t examples\08-third-party-rich -i examples\08-third-party-rich\config.yaml -o examples\08-third-party-rich\generated
```

## 要点

- `from rich.tree import Tree` 写在 `models.py`，不要写在 `.j2` 模板里。
- `rich` 默认面向终端；本示范用 `Console(file=StringIO())` 把树形结构导出为字符串。
- 模板目录下不要有名为 `rich.py` 或 `rich/` 的文件，否则会挡住真正的 `rich` 包。

## 预期输出

`generated/out` 中应包含以 `jinja-build` 为根、`models.py` 等为子节点的树形文本。

## 回到总览

[examples/README.md](../README.md)
