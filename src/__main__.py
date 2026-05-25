import argparse

from _core import Core


def get_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-t", "--template", type=str, help="输入jinja2模板目录")
    parser.add_argument("-o", "--output", type=str, help="输出文件或目录")
    parser.add_argument(
        "-mf",
        "--models-filename",
        type=str,
        default="models.py",
        help="python数据结构文件名",
    )
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("-i", "--input", type=str, help="输入配置文件")
    input_group.add_argument("-b", "--batch", nargs="+", type=str, help="批处理输入配置文件列表")
    args = parser.parse_args()
    return args


def main(batch: list[str] | None, **kwargs: object) -> None:
    """按单次参数或批处理配置执行构建。"""
    Core(batch=batch, **kwargs).run()


if __name__ == "__main__":
    args = get_args()
    main(**vars(args))
