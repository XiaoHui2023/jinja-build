# 05 · models.py 引用其它 Python 模块

`models.py` 不必写满所有逻辑，可把工具函数放在同目录包内，用**绝对导入**（包名从模板根目录起）。

## 目录结构

```text
05-models-imports/
  models.py          # from demo_lib.formats import …
  demo_lib/
    __init__.py
    formats.py
  config.yaml
  out.j2
```

加载 `models.py` 时，工具会把**该文件所在目录**加入 `sys.path`，并在整次构建（含模板渲染、`@property` 求值）期间保持，因此同目录模块可在顶层或函数内延迟 `import`。请使用 `from demo_lib.xxx import …`，不要依赖仓库外的已安装包名。

## 生成

```bat
example.bat 05-models-imports
```

## 要点

- 辅助模块放在与 `models.py` 同级或子包中，并保留 `__init__.py`（Python 3.3+ 命名空间包亦可，本示范用常规包）。
- `models.py` 里最后一类仍是输入主类 `Data`。
- 从 `formats` 引入的函数可在类方法里调用，方法同样可作模板过滤器。

## 下一步

[06-config-variables](../06-config-variables/README.md)
