# 打包工具

## 一键打包（PyInstaller；Linux 再 staticx）

在仓库根执行（使用根目录 `.venv`，无则创建）：

```bash
chmod +x tools/pack.sh
./tools/pack.sh
```

默认构建全部入口。只打某一个时传入 `src` 或 `schema`：

```bash
./tools/pack.sh src
./tools/pack.sh schema
```

Linux 另需系统安装 **`patchelf`**（如 `sudo apt install patchelf`）。产物写入 `dist/`：

| 目标 | 产物 |
| --- | --- |
| 主入口（src） | `jinja-build` / `jinja-build.exe` |
| 结构说明（schema） | `jinja-build-schema` / `jinja-build-schema.exe` |

Linux 上为 staticx 处理后的单文件；Windows 为 PyInstaller onefile，无 staticx 步骤。**macOS** 当前脚本跳过 staticx，仅 PyInstaller 产物。

更完整的说明见仓库根目录 [PACKAGING.md](../PACKAGING.md)。
