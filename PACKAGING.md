# 离线打包

仓库不再提供 Docker 镜像或 CI 自动打包产物。需要发布时，在有网络的机器上先下载 PyInstaller 和项目运行依赖，再把仓库与依赖目录一起放到目标离线环境中自行打包。

## 在线下载依赖

在联网环境执行：

```bash
bash packaging/download-pyinstaller-deps.sh
```

脚本会把 wheel 文件下载到 `packaging/wheels/`。如果要下载到其他目录，可以传入目标路径：

```bash
bash packaging/download-pyinstaller-deps.sh /tmp/jinja-build-wheels
```

下载完成后，把仓库源码和这个 wheels 目录一起拷贝到离线环境。

## 离线打包

离线环境需要提前安装 Python 3.10 或更新版本。进入仓库根目录后执行：

```bash
bash packaging/build-pyinstaller.sh
```

默认会打包全部入口，产物写入 `dist/`：

- `jinja-build`：CLI 入口
- `jinja-build-server`：服务端入口
- `jinja-build-doc`：文档监听入口

也可以只打包某一个入口：

```bash
bash packaging/build-pyinstaller.sh cli
bash packaging/build-pyinstaller.sh server
bash packaging/build-pyinstaller.sh doc
```

如果 wheels 不在默认的 `packaging/wheels/`，可以指定：

```bash
WHEEL_DIR=/path/to/wheels bash packaging/build-pyinstaller.sh
```

## Spec 文件

PyInstaller spec 文件放在 `packaging/specs/`：

- `jinja-build-cli.spec`
- `jinja-build-server.spec`
- `jinja-build-doc.spec`

`server` 会复用 `cli` 的核心渲染逻辑，所以 `jinja-build-server.spec` 已经把 `cli` 加入 `pathex`。

## 兼容边界

Linux 单文件产物的兼容性取决于实际执行 PyInstaller 的机器。要支持 Ubuntu 16.04，应在 Ubuntu 16.04 x86_64 或 glibc 基线不高于 2.23 的环境中运行离线打包脚本。

如果在较新的 Ubuntu 上打包，产物可能无法在 Ubuntu 16.04 上运行。Ubuntu 14.04 或更旧版本、非 x86_64 架构、musl 系统或模板代码额外依赖的系统动态库，都需要单独验证。
