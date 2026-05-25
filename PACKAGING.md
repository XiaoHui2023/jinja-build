# 打包发布

需要发布可执行文件时，在可访问 PyPI 的机器上于仓库根执行一键脚本；Linux 上会在 PyInstaller onefile 之后再做 staticx，得到更易在旧 glibc 环境运行的自解压单文件。

## 一键打包

```bash
./tools/pack.sh
```

Windows 上若无法直接执行，可用 `bash tools/pack.sh`。

脚本会创建或复用根目录 `.venv`，执行 `pip install -e .` 安装项目依赖，再调用 PyInstaller。详细参数与单入口构建见 [tools/README.md](tools/README.md)。

| 命令 | 产物（`dist/`） |
| --- | --- |
| `./tools/pack.sh` 或 `all` | `jinja-build` 与 `jinja-build-schema` |
| `./tools/pack.sh src` | `jinja-build` |
| `./tools/pack.sh schema` | `jinja-build-schema` |

Windows 产物为 `*.exe`，无 staticx 步骤。

## Linux staticx

在 Linux 上，`tools/pack.sh` 对每个 ELF 产物再运行 **staticx**，需要系统已安装 **patchelf**（例如 `sudo apt install patchelf`）。**macOS** 当前跳过 staticx，仅保留 PyInstaller onefile。

## Spec 文件

PyInstaller 规格放在仓库根目录：

- `jinja-build-cli.spec` → `jinja-build`
- `jinja-build-schema.spec` → `jinja-build-schema`

## 兼容边界

单文件可执行文件的系统兼容性取决于**执行打包的那台机器**。要支持较旧的 Linux 发行版，应在 glibc 基线不高于目标环境的系统上构建，并在目标机实测 staticx 产物。模板或用户代码若依赖额外系统动态库，也需单独验证。
