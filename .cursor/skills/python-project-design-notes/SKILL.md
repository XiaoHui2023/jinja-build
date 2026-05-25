---
name: python-project-design-notes
description: >-
  jinja-build：Agent 当前有效的设计意图与硬性要求（三件套之一）。
  变更历史见 python-project-changelog；预加载见 python-project-session-manifest。用户根写法见 agent-project-design-notes。
---

# 设计笔记（当前有效）

> 何时、为何变更见 **`.cursor/skills/python-project-changelog/SKILL.md`**。若与 changelog 冲突，**以 changelog 最新条目为准**。

## 设计意图（像设计图）

**jinja-build** 用 Jinja2 把「模板 + 输入配置 + 模板目录内的 `models.py`」生成一组输出文件。两个入口：

| 入口 | 目录 | 职责 |
| --- | --- | --- |
| 主功能 | `src/` | 本地渲染：`-t` 模板、`-i`/`-b` 输入、`-o` 输出 |
| 结构说明 | `schema/` | 扫描模板根，为含 `models.py` 的仓库生成/监听 Markdown 结构说明 |

**不做**：HTTP 服务、callback 编排、Verilog filelist、捆绑 rg/fd。

代码按入口分目录（`src/`、`schema/`），`__main__.py` 为脚本入口；包内用 `_` 前缀模块（主入口 `from _core import Core`，结构说明 `from _schema import Schema`）。**非** setuptools 单包 `src layout`（无 `src/jinja_build/` 包名目录）。

## 主入口 · 数据流与模板环境

```text
输入配置 -> models.py 末类实例 -> to_dict(含 property) -> 模板上下文
                |
                +-> 全局：models 中各类名 + 主类公开实例方法（函数调用语法）
                +-> 过滤器：内置常用函数 + 主类公开实例方法（管道语法）
```

- **主数据类**：`models.py` 中**最后一个** `class` 为输入配置实例化的类型；其前的类注册为模板**全局**（类型名 -> 类对象），供模板引用类型本身。
- **渲染环境**：`StrictUndefined`；`jinja2.ext.do`、`loopcontrols`；`SafeDictEnvironment` 对 dict 优先按键访问。
- **搜索路径**：模板所在目录 + 模板根（目录模式为 `-t` 指向的目录）。

## 主入口 · 过滤器（硬性）

1. **内置过滤器**：每个模板环境自动注册一组常用函数（`replace`、`upper`、`lower`、`strip`、`len`、`min`、`max`、`sorted`、`sum`、`format`、`split`、`join` 等），语法为 **`{{ 值 | 过滤器名(参数…) }}`**。实现见 `src/_utils/_filters.py` 的 `build_builtin_filters()`；在 `get_env` 中写入 `env.filters`。
2. **models.py 实例方法作过滤器**：主数据类上**非 `_` 开头**的**普通实例方法**（`inspect.isfunction`）同时注册为过滤器，绑定当前输入实例；管道左侧值忽略，参数传给方法。例：`def title(self): …` → `{{ '' | title }}` 或保留 **`{{ title() }}`** 全局调用（向后兼容）。
3. **不再**把整个 `builtins` 注入模板全局；常用能力走过滤器。`len` 等仍可通过过滤器或 Jinja 自带 `length` 使用；`BASE_GLOBALS` 仅保留少量全局（如 `len`）供 `{{ len(items) }}` 旧模板。
4. **类函数范围**：仅主数据类（`class_map[-1]`）上定义的函数；不自动收集继承自第三方基类的无关方法。

## 主入口 · property 与模板变量（硬性）

- `to_dict` 在序列化 **Pydantic `BaseModel`、dataclass、普通实例** 时，除字段/属性外须合并 **`@property` 只读值**（`type(obj)` 上 `property` 描述符），**不覆盖**已有同名字段。
- 模板中 **`{{ label }}`** 直接读 property，与字段同级；**不要**把 property 当成过滤器。

## 主入口 · 原有设计特性（用户向行为摘要）

### 模板目录

- `-t` 可为目录或单文件；目录模式 `rglob("*.j2")`，输出保留相对层级。
- 目录内默认 `models.py`（`-mf` 可改）。

### 数据建模

- 配置经 `configlib.load_config` 载入为 dict，再 `主类(**data)` 实例化。
- 模板侧拿到的是整理后的 dict（含嵌套结构与 property），不是原始配置文件。

### 空白输出

- 渲染结果 `strip()` 后为空则**不写文件**、不创建空目录。

### 批量渲染

- `-b` 与 `-i` 互斥；每项输入输出到 `output/<输入文件 stem>/`。
- stem 重复时 `ValidationError`。

### 并行

- 任务 = 输入 × 模板；`ThreadPoolExecutor`，`max_workers = min(任务数, cpu_count)`。

### 导入隔离

- `models.py` 经 `importlib` 私有模块名加载；加载时临时把 `models.py` 父目录插入 `sys.path`，结束后恢复。
- 同目录 `helper.py` 等可在 `models.py` 里 import；不同模板目录的 models 模块名隔离。

### 主入口参数（与 `src/__main__.py` 一致）

| 长参数 | 短参数 | 说明 |
| --- | --- | --- |
| `--template` | `-t` | 模板目录或单文件 |
| `--output` | `-o` | 输出路径或批处理根目录 |
| `--input` | `-i` | 单份输入配置；省略则空 dict |
| `--batch` | `-b` | 多份输入，与 `-i` 互斥 |
| `--models-filename` | `-mf` | 默认 `models.py` |

## Schema · 设计特性摘要

- 在 `-t` 根下找含 `models_filename` 的目录为**仓库**；发现后不再向子层拆仓库。
- 每仓库独立指纹与生成；单仓失败不阻塞其他仓；失败后内容未变则不反复重试。
- 默认 `run_once`；`-w` 持续监听，`-i` 间隔秒数。
- 生成结束后再查变更，渲染期间有改动则**补跑一次**。
- 支持 Pydantic 与 dataclass，输出 Markdown 字段表；逻辑在 `schema/_schema/`。
- 门面类 **`Schema`**（`schema/_schema/_core.py`）。

| 长参数 | 短参数 | 说明 |
| --- | --- | --- |
| `--template` | `-t` | 模板根 |
| `--output` | `-o` | 文档输出根 |
| `--log` | `-l` | 日志目录 |
| `--models-filename` | `-mf` | 默认 `models.py` |
| `--interval` | `-i` | 监听间隔，默认 `1.0` |
| `--watch` | `-w` | 持续监听 |

## 来自用户/团队的硬性要求

1. **依赖**：`Jinja2`、`pydantic`、`python-library-configlib==0.1.0`；`packages = []`，`pip install -e .` 只拉依赖。
2. **开发脚本**：Windows 用 `update.bat`、`test.bat`、`example.bat <示范名>`；Linux/macOS/Git Bash 用 `update.sh`、`test.sh`、`example.sh <示范名>`。均在仓库根 `.venv` 下执行；测试为 `python -m unittest discover -s tests`。
3. **文档分工**：用户向 `src/README.md`、`schema/README.md`、`docs/`（子文档索引见 `docs/README.md`，如 `docs/models-py.md`）；Agent 口径**只**在本 skill；禁止把本 skill 全文抄进源码注释或 README。
4. **中文措辞**：`forbidden-doc-comment-vocabulary`；README 文首不写命令表。

## 打包（PyInstaller + staticx）

- `tools/pack.sh`：`all` | `src` | `schema`；`.venv` + `pip install -e .` + PyInstaller；Linux 再 staticx（`patchelf`）。
- 根目录 `jinja-build-cli.spec`（主入口）、`jinja-build-schema.spec`；`upx=False`；无 `tools/bin` 捆绑。
- 可执行名：`jinja-build`、`jinja-build-schema`。

## 与当前实现的对齐

- **过滤器注册**：`get_env` 先 `build_builtin_filters()`，再合并当次输入的 `build_model_method_filters`。
- **全局方法**：`_build_template_extras` 仍暴露 `title()` 等函数调用，与过滤器双轨。

## 示范仓库 `examples/`（教学）

- 索引：[examples/README.md](../../examples/README.md)；子目录 `01`～`06`，各含 README、`models.py`、`config.yaml`、`.j2`。
- 生成：`example.bat <目录名>` 或 `example.sh <目录名>`（**无** run-all）；产物在 `examples/<名>/generated/`（gitignore）。
- 内置过滤器不覆盖 Jinja 自带 `sum`/`min`/`max`/`sorted`。

## 备忘与待定

- 根目录总览 README 待定。
- `staticmethod` / `classmethod` 是否纳入过滤器：当前仅普通实例方法。
- Windows 可选 `tools/pack.bat`。
