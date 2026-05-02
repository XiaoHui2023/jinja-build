# jinja-build Packaging

`packaging` 目录用于把 jinja-build 的三个入口打成 PyInstaller 单文件产物，适合先在联网环境准备依赖，再带到离线环境构建。

- `jinja-build`：本地 CLI 渲染入口。
- `jinja-build-server`：HTTP 渲染服务入口。
- `jinja-build-doc`：模板数据结构文档生成入口。
- 依赖 wheel 可以提前下载，离线构建时不再访问网络。
- 构建结果统一写入仓库根目录的 `dist/`。

## 使用方式

### 在线准备依赖

在可以访问 Python 包源的机器上执行：

```bash
bash packaging/download-pyinstaller-deps.sh
```

默认会把 wheel 文件下载到 `packaging/wheels/`。如果要放到其他目录，可以传入目标路径：

```bash
bash packaging/download-pyinstaller-deps.sh /tmp/jinja-build-wheels
```

下载完成后，把仓库源码和 wheel 目录一起放到离线构建环境。

### 离线构建

离线环境需要有 Python 3.10 或更新版本。进入仓库根目录后执行：

```bash
bash packaging/build-pyinstaller.sh
```

默认会构建全部入口：

| 目标 | 产物 |
| --- | --- |
| CLI | `dist/jinja-build` |
| Server | `dist/jinja-build-server` |
| Doc | `dist/jinja-build-doc` |

只想构建某个入口时，把目标名传给脚本：

```bash
bash packaging/build-pyinstaller.sh cli
bash packaging/build-pyinstaller.sh server
bash packaging/build-pyinstaller.sh doc
```

### 自定义位置

wheel 不在默认目录时，用 `WHEEL_DIR` 指向实际位置：

```bash
WHEEL_DIR=/path/to/wheels bash packaging/build-pyinstaller.sh
```

需要指定 Python 解释器时，用 `PYTHON`：

```bash
PYTHON=python3.11 bash packaging/download-pyinstaller-deps.sh
PYTHON=python3.11 bash packaging/build-pyinstaller.sh
```

构建虚拟环境默认放在仓库根目录的 `.venv-pyinstaller/`。需要换位置时，用 `VENV_DIR`：

```bash
VENV_DIR=/tmp/jinja-build-pyinstaller bash packaging/build-pyinstaller.sh
```

## 设计特性

### 离线依赖

依赖准备和实际构建分成两个脚本。

```text
联网机器 -> 下载 wheels -> 离线机器 -> PyInstaller 构建
```

这样离线环境只需要拿到源码和 wheel 目录，不需要临时访问包源。

### 入口拆分

三个入口各自有 PyInstaller spec 文件。

| spec | 产物 |
| --- | --- |
| `specs/jinja-build-cli.spec` | `jinja-build` |
| `specs/jinja-build-server.spec` | `jinja-build-server` |
| `specs/jinja-build-doc.spec` | `jinja-build-doc` |

默认构建全部入口，也可以按 `cli`、`server`、`doc` 单独构建。

### 环境复用

构建脚本会复用专门的 PyInstaller 虚拟环境。

第一次运行时会创建环境并安装本地 wheel 依赖；后续运行继续复用这个环境。每次构建前会清理 `build/` 和 `dist/`，避免旧产物混在一起。

## 兼容边界

PyInstaller 单文件产物的系统兼容性取决于实际执行构建的机器。要面向较旧 Linux 发行版发布，应在 glibc 基线不高于目标环境的机器上构建。

模板代码如果额外依赖系统动态库，也需要在目标环境单独验证。
