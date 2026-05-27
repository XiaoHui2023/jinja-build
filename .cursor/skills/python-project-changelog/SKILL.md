---
name: python-project-changelog
description: >-
  jinja-build：按时间记录要求与决议；最新在上；矛盾以最新为准；过多时压缩旧段。
  当前有效口径见 python-project-design-notes。
---

# jinja-build · 变更记录

（最新在上。规则见 `~/.cursor/skills/agent-project-changelog/SKILL.md`。）

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
