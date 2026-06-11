---
name: python-project-session-manifest
description: >-
  jinja-build 三件套之一：会话预加载顺序与「用过的 skill」。设计笔记与 changelog 为另两个项目内 skill。
---

# 预加载 · 会话清单

## 初始化加载（Session preload）

在本仓库开展实质性工作前，按顺序 **Read**（`~` 为 `~/.cursor/skills`）：

1. `~/.cursor/skills/python-project-ai/SKILL.md`
2. `~/.cursor/skills/project-skill-manifest-policy/SKILL.md`
3. `.cursor/skills/python-project-design-notes/SKILL.md`
4. `.cursor/skills/python-project-changelog/SKILL.md`
5. `~/.cursor/skills/python-doc-comments/SKILL.md`
6. `~/.cursor/skills/python-script-environment-variables/SKILL.md`

可选（改动较多时）：

7. `~/.cursor/skills/agent-codegen-self-review/SKILL.md`

**本仓库无** `api`/`impl` callback 分层；勿预加载 `callback-api-impl-layers`、`impl-sink-rich-logging` 等，除非 design-notes 明确要求。

**新增**预加载项：追加到本节。维护列表时 Read **`~/.cursor/skills/agent-project-preload/SKILL.md`**。

## 本仓库预加载维护说明

- 仅改「初始化加载」列表；口径与 changelog 写法见用户根 **`agent-project-design-notes`**、**`agent-project-changelog`**。
- 首次为三件套建库：Read **`agent-project-init`**（一次性）。

## 同伴 skill 存放约定

- **默认**：`~/.cursor/skills/<name>/SKILL.md`，除非用户要求写在项目下。
- **项目内**仅保留三件套：本文件、**design-notes**、**changelog**。

## 用过的 skill（追加记录）

- agent-project-init | `~/.cursor/skills/agent-project-init/SKILL.md`
- agent-project-preload | `~/.cursor/skills/agent-project-preload/SKILL.md`
- agent-project-design-notes | `~/.cursor/skills/agent-project-design-notes/SKILL.md`
- agent-project-changelog | `~/.cursor/skills/agent-project-changelog/SKILL.md`
- python-project-ai | `~/.cursor/skills/python-project-ai/SKILL.md`
- project-skill-manifest-policy | `~/.cursor/skills/project-skill-manifest-policy/SKILL.md`
- agent-codegen-self-review | `~/.cursor/skills/agent-codegen-self-review/SKILL.md`
- forbidden-doc-comment-vocabulary | `~/.cursor/skills/forbidden-doc-comment-vocabulary/SKILL.md`
- python-pyinstaller-staticx-packaging | `~/.cursor/skills/python-pyinstaller-staticx-packaging/SKILL.md`
- python-rich-terminal-colors | `~/.cursor/skills/python-rich-terminal-colors/SKILL.md`
- doc-surface-roles-zh | `~/.cursor/skills/doc-surface-roles-zh/SKILL.md`
- doc-surface-topic-page-zh | `~/.cursor/skills/doc-surface-topic-page-zh/SKILL.md`
