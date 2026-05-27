# 打包工具

## 一键打包（PyInstaller；Linux 再 staticx）

在仓库根执行（使用根目录 `.venv`，无则创建）：

### Linux / macOS / Git Bash

```bash
./tools/pack.sh
```

### Windows

```bat
tools\pack.bat
```

无法直接执行 `pack.sh` 时，也可用 Git Bash：`bash tools/pack.sh`。

产物写入 `dist/`：

| 目标 | 产物 |
| --- | --- |
| 主入口（src） | `jinja-build` / `jinja-build.exe` |

| 平台 | 脚本 | staticx |
| --- | --- | --- |
| Linux | `pack.sh` | 需要系统 **patchelf** |
| macOS 等 | `pack.sh` | 跳过 |
| Windows | `pack.bat` / `pack.sh` | 跳过 |

更完整的说明见仓库根目录 [PACKAGING.md](../PACKAGING.md)。
