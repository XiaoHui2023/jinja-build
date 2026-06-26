# 示范仓库

本目录按难度排列多个**独立模板仓库**，用于学习 Jinja2 语法与 jinja-build 的 `models.py`、配置文件用法。每个子目录自带说明，并可用主入口 `src` 生成产物。

## 学习顺序

| 目录 | 主题 |
| --- | --- |
| [01-jinja-basics](01-jinja-basics/README.md) | Jinja 基础语法（变量、分支、循环、set、空白控制、include 等） |
| [02-filters](02-filters/README.md) | 管道过滤器、内置过滤器、`models.py` 中的过滤函数与 property |
| [03-macros-advanced](03-macros-advanced/README.md) | macro、call、extends/block、import |
| [04-optional-output](04-optional-output/README.md) | 用开关控制是否生成某个文件（空白结果自动跳过） |
| [05-models-imports](05-models-imports/README.md) | `models.py` 引用同目录 Python 包（绝对导入） |
| [06-config-variables](06-config-variables/README.md) | 配置文件中的 `${}` 变量引用 |
| [07-multifile-config](07-multifile-config/README.md) | 多文件配置：`# 文件名` 捆绑与 `!include` |
| [08-third-party-rich](08-third-party-rich/README.md) | `models.py` 导入第三方库 `rich`（含打包 smoke） |

## 生成方式

将 `01-jinja-basics` 换成其它示范目录名即可。

### Windows

```bat
example.bat 01-jinja-basics
```

或：

```bat
.venv\Scripts\python.exe src\__main__.py -t examples\01-jinja-basics -i examples\01-jinja-basics\config.yaml -o examples\01-jinja-basics\generated
```

### Linux / macOS / Git Bash

```bash
chmod +x update.sh example.sh
./update.sh
./example.sh 01-jinja-basics
```

或：

```bash
.venv/bin/python src/__main__.py \
  -t examples/01-jinja-basics \
  -i examples/01-jinja-basics/config.yaml \
  -o examples/01-jinja-basics/generated
```

产物写在各示范目录下的 `generated/`（已加入 `.gitignore`）。生成后请直接打开 `generated/` 里的文本对照 README 阅读。
