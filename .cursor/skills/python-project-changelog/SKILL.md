---
name: python-project-changelog
description: >-
  jinja-build：按时间记录要求与决议；最新在上；矛盾以最新为准；过多时压缩旧段。
  当前有效口径见 python-project-design-notes。
---

# jinja-build · 变更记录

（最新在上。规则见 `~/.cursor/skills/agent-project-changelog/SKILL.md`。）

## 2026-06-26

- **决议**：发行压缩包纳入 `examples/`（排除 `generated/`）；示范目录去掉序号前缀并重写各 README。
- **决议**：PyInstaller `hiddenimports` 用 `collect_submodules("rich")`，修复 `models.py` 动态 `import rich.tree` 在 frozen 可执行文件中失败。
- **决议**：新增示范 `examples/third-party-rich`；Release CI smoke 增加对该示范的 frozen 渲染检查。

## 2026-06-20

- **决议**：GitHub Release 切 **滚动自动发布**（push `main` 覆盖 `v{version}` tag 与附件）；workflow 触发由 tag 改为 `branches: [main]`。
- **决议**：Linux CI 恢复 **staticx**（`ci_pack_ubuntu16.sh` 去掉 `PACK_LINUX_SKIP_STATICX=1`）；Ubuntu 16.04 上 **从源码安装 staticx**（`--no-binary=staticx`）并 `readelf` 自检，修复 wheel bootloader 在旧 objcopy 下 exit 139。

## 2026-06-19

- **决议**：输入配置依赖 **configlib 0.1.7**；`config.md` 同步 CSV 字典表格式说明。

## 2026-06-16

- **决议**：整次 `Core.run()` 通过 `models_import_path` 保持 `models.py` 父目录在 `sys.path`，支持 `@property` / 方法内的**延迟导入**；单独 `load_module` 仍临时加路径后恢复。
- **决议**：并行渲染（输入 × 模板）有多处失败时 **只展示一张** Rich 错误卡片；`Core._render_all` 汇总 `RenderFailure` 后按入口模板路径字典序取首个展示。

## 2026-06-11

- **决议**：根 **`model.md`** 定稿：开篇两条列表（末类入口、递归 `*.j2`）；Pydantic / dataclass / 普通类仅最小示例；**过滤器**四分列表；**导入子脚本**（绝对路径、可无 `__init__.py`）；**可选文件**（渲染结果为空时不写盘）。口径写入 **design-notes**「用户向 model.md 专档」与 **`doc-surface-topic-page-zh`**。
- **决议**：删除 **`PACKAGING.md`**；打包说明收进 **`tools/pack.sh`** / **`pack.bat`** 头注释；**`tools/bundle_release.py`** 将可执行文件与 **README.md** / **config.md** / **model.md** 打成发行压缩包。
- **决议**：根目录用户向 **README.md** / **config.md** / **model.md** 分工：README 演示全流程与 CLI，专档写配置语法与 **models.py** 写法。
- **决议**：`-t` / `--template` 仅接受模板目录；传入单个 `.j2` 文件时 `NotADirectoryError`。

## 2026-06-10

- **决议**：`@property` 与 models 实例方法在渲染期求值失败时 **必须报错**；`read_property_value` 不再吞异常；`print_render_user_error` 展示模板行与用户 `models.py` 行。

## 2026-05-27

- **决议**：输入配置支持 `#<文件名>` 单文件捆绑（`src/_utils/_config_bundle.py`）；`!include` 与 `${}` 由 **configlib 0.1.3** 提供；示范 `examples/multifile-config`。
- **决议**：移除自创环境变量 **`JINJA_BUILD_THEME`**；错误配色仅 **`--theme`**（默认 `auto`）。用户根新增 **`python-script-environment-variables`** skill；已列入预加载与 **`agent-project-preload`** Python 表。

## 2026-05-26

- **决议**：新增 **`tools/pack.bat`**，与 **`tools/pack.sh`** 并列；Windows 用 `tools\pack.bat`，Unix 用 `./tools/pack.sh`；更新 **`PACKAGING.md`**、**`tools/README.md`** 与用户根 **`python-pyinstaller-staticx-packaging`** skill。
- **决议**：删除 **`schema/`**、遗留 **`doc/`**、**`docs/`**、**`jinja-build-schema.spec`**、**`tests/test_schema.py`**；项目不再为模板仓库生成或维护 Markdown 结构说明，文档由用户在各模板仓库自行管理。
- **决议**：**`tools/pack.sh`** 仅打主入口 **`jinja-build`**（`jinja-build-cli.spec`）；移除 `schema` / `all` 打包目标。

## 2026-05-21

- **决议**：`cli/` 改名为 **`src/`**（主功能）；`doc/` 改名为 **`schema/`**（按仓库生成结构说明）；内部包 `_doc` → `_schema`，类 `Doc` → `Schema`；打包目标 `src`/`schema`，可执行文件 `jinja-build-schema`（`jinja-build-doc.spec` → `jinja-build-schema.spec`）；测试 `test_schema.py`。
- **要求**：新增用户向 `docs/`；首篇 `docs/models-py.md` 说明 Pydantic 严格配置（`extra='forbid'`、`strict=True`）使配置错键/错类型在构建时报错。

## 2025-05-20

- **决议**：删除用户根 **`agent-project-requirements-notes`**（不再保留兼容重定向）；设计笔记以 **`agent-project-design-notes`** 为准。
- **决议**：用户根 skill 拆分为 **`agent-project-init`**（一次性初始化）、**`agent-project-preload`**、**`agent-project-design-notes`**、**`agent-project-changelog`**；`python-project-ai` 不再含三件套模板；日常预加载不再 Read 用户根 changelog skill。
- **决议**：项目 Agent 协作采用**三件套**：`python-project-session-manifest`（预加载）、`python-project-design-notes`、`python-project-changelog`（本文件）。
- **决议**：`examples/` 不提供 run-all；仅用 `example.bat` / `example.sh <示范名>` 生成单个示范。
- **要求**：tests 补充复杂组合用例（`test_core_integration.py`、`test_jinja_unit.py`、`_case.py`）。

## 2025-05-19

- **决议**：移除 **server** 入口及 `jinja-build-server` 打包；仅 **CLI** + **Doc**。
- **要求**：CLI 增加内置过滤器 + `models.py` 方法作过滤器；`@property` 作模板变量。
- **决议**：新增 `examples/` 六个循序示范仓库及双平台 `example`/`update`/`test` 脚本。

## 2025-05-18

- **决议**：打包对齐同级 **filelist_fix**：根目录 `jinja-build-*.spec`、`tools/pack.sh`、`.venv` + PyInstaller；Linux **staticx**；废除 `packaging/` 离线 wheel 流程。
- **决议**：`.cursor/skills/` 引入 `python-project-session-manifest` 与 `python-project-design-notes`（当时为两件套，已由 2025-05-20 扩展为三件套）。
