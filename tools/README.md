# 打包工具

## 一键打包（PyInstaller；Linux 再 staticx）

在仓库根执行（使用根目录 `.venv`，无则创建）：

```bash
./tools/pack.sh
```

Windows 上若无法直接执行，可用 `bash tools/pack.sh`。

产物写入 `dist/`：

| 目标 | 产物 |
| --- | --- |
| 主入口（src） | `jinja-build` / `jinja-build.exe` |

Linux 上为 staticx 处理后的单文件；Windows 为 PyInstaller onefile，无 staticx 步骤。**macOS** 当前脚本跳过 staticx，仅 PyInstaller 产物。

Linux 另需系统安装 **`patchelf`**（如 `sudo apt install patchelf`）。

更完整的说明见仓库根目录 [PACKAGING.md](../PACKAGING.md)。
