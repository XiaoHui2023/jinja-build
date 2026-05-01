import argparse

from _server import run_server


def get_args() -> argparse.Namespace:
    """解析服务端启动参数。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, required=True, help="监听端口")
    parser.add_argument("-t", "--template", type=str, required=True, help="服务端模板根目录")
    parser.add_argument("-l", "--log", type=str, required=True, help="服务端日志目录")
    return parser.parse_args()


def main() -> None:
    """启动服务端。"""
    args = get_args()
    run_server(
        port=args.port,
        template_root=args.template,
        log=args.log,
    )


if __name__ == "__main__":
    main()
