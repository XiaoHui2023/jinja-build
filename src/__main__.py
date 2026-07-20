import argparse

from _core import Core
from _utils._cli_user_error import AlreadyReportedError
from _utils._jinja_rich import configure_jinja_error_theme


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
    parser.add_argument("-i", "--input", type=str, help="输入配置文件或配置文件目录")
    parser.add_argument(
        "--debug-input",
        type=str,
        metavar="PATH",
        help="将配置文件解析结果（尚未实例化 models）写出为 PATH；相对路径相对当前工作目录",
    )
    parser.add_argument(
        "--debug-models",
        type=str,
        metavar="PATH",
        help="将 models 实例化后的模板数据（渲染前）写出为 PATH；相对路径相对当前工作目录",
    )
    parser.add_argument(
        "--theme",
        choices=("auto", "light", "dark", "none"),
        default="auto",
        help="错误配色：auto 仅读终端 COLORFGBG、否则 dark；light/dark/none 显式指定",
    )
    args = parser.parse_args()
    return args


def main(**kwargs: object) -> None:
    """按单次输入或目录输入执行构建。"""
    Core(**kwargs).run()


if __name__ == "__main__":
    args = get_args()
    configure_jinja_error_theme(args.theme)
    run_kwargs = {key: value for key, value in vars(args).items() if key != "theme"}
    try:
        main(**run_kwargs)
    except AlreadyReportedError:
        raise SystemExit(1) from None
