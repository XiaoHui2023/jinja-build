# jinja-build Docker 离线包

## 用途

这个包用于在离线 Ubuntu 机器上运行 jinja-build。容器里会同时启动服务端和文档生成器。

服务端提供渲染接口。文档生成器会持续监听模板目录，并把数据结构文档写到输出目录。

## 目录

| 路径 | 说明 |
| --- | --- |
| `template/` | 放模板仓库，容器只读挂载 |
| `doc-output/` | 文档生成器写出的 Markdown |
| `log/` | 服务端和文档生成器日志 |
| `docker-compose.yml` | 离线运行配置 |
| `load-and-run.sh` | 加载镜像并启动容器 |

## 运行

先把模板放到 `template/` 目录，然后执行：

```bash
chmod +x ./load-and-run.sh
./load-and-run.sh
```

脚本会加载当前目录里的镜像归档，并启动容器。

## 访问

默认端口是 `8000`。渲染请求地址：

```bash
curl -OJ -X POST "http://127.0.0.1:8000/render" \
  -F "template=site" \
  -F "input=@input.json"
```

如果模板路径指向目录，响应是 zip。若指向单个模板文件，响应是渲染后的文件。

## 配置

| 环境变量 | 说明 | 默认 |
| --- | --- | --- |
| `PORT` | 宿主机暴露端口。 | `8000` |
| `MODELS_FILENAME` | 模板仓库里的数据结构文件名。 | `models.py` |
| `DOC_INTERVAL` | 文档生成器检查模板变化的间隔秒数。 | `1.0` |

修改配置后重新执行：

```bash
docker compose up -d
```
