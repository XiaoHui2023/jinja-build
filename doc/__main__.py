import argparse

from _doc import Doc
from _doc._logging import configure_logging


def get_args() -> argparse.Namespace:
    """解析文档生成参数。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--template", type=str, required=True, help="要监听的模板根目录")
    parser.add_argument("-o", "--output", type=str, required=True, help="文档输出根目录")
    parser.add_argument("-l", "--log", type=str, required=True, help="日志输出目录")
    parser.add_argument(
        "-mf",
        "--models-filename",
        type=str,
        default="models.py",
        help="用于识别仓库的数据结构文件名",
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=float,
        default=1.0,
        help="检查目录变化的间隔秒数",
    )
    return parser.parse_args()


def main() -> None:
    """启动文档生成器。"""
    args = get_args()
    log_path = configure_logging(args.log)
    doc = Doc(
        template=args.template,
        output=args.output,
        models_filename=args.models_filename,
        interval=args.interval,
    )
    print(f"doc log: {log_path}")
    doc.run()


if __name__ == "__main__":
    main()
