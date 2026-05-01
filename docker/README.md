# Docker 离线发布

## 设计特性

### 单目录收口

Docker 相关文件都放在这个目录里。仓库根目录只作为构建上下文，便于镜像复制源码和读取项目依赖。

离线包也从这里的配置生成。发布时不需要离线机器重新构建镜像。

### 双任务容器

容器启动后会同时运行服务端和文档生成器。服务端处理渲染请求，文档生成器持续监听模板目录并写出 Markdown。

任一任务退出时，启动器会停止另一个任务。这样容器状态能反映整体服务是否还健康。

### 离线加载

GitHub Actions 会把镜像保存成归档，并和运行配置、启动脚本一起打包。离线机器只需要 Docker，不需要 Python、pip 或源码。

离线包里的运行脚本会先加载镜像，再按 compose 配置启动容器。

## 配置

### `PORT`

| 参数 | 说明 | 默认 |
| --- | --- | --- |
| `PORT` | 宿主机访问服务端时使用的端口。 | `8000` |

### `MODELS_FILENAME`

| 参数 | 说明 | 默认 |
| --- | --- | --- |
| `MODELS_FILENAME` | 模板仓库里的数据结构文件名。 | `models.py` |

### `DOC_INTERVAL`

| 参数 | 说明 | 默认 |
| --- | --- | --- |
| `DOC_INTERVAL` | 文档生成器检查模板变化的间隔秒数。 | `1.0` |

## 本地构建

在仓库根目录执行：

```bash
docker/build-offline-package.sh 0.1.0
```

产物会写到：

```text
artifacts/jinja-build-docker-0.1.0.tar.gz
```

## GitHub Actions

`Build Docker Offline Package` 工作流会在手动触发或推送 `v*` 标签时运行。

手动触发时填写版本号，例如 `0.1.0`。推送标签时会使用标签名，并去掉开头的 `v`。

手动触发只上传 Actions artifact。推送标签会同时创建 GitHub Release，并把离线包放进 Release 附件。

离线包下载后拷到 Ubuntu 机器，解压并运行：

```bash
chmod +x ./load-and-run.sh
./load-and-run.sh
```
