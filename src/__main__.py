from _core import Core
import argparse
from _utils import configlib


def get_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-t", "--template", type=str, help="输入jinja2模板目录")
    parser.add_argument("-i", "--input", type=str, help="输入json/yaml配置文件")
    parser.add_argument("-o", "--output", type=str, help="输出文件或目录")
    parser.add_argument("-mf", "--models-filename", type=str, help="python数据结构文件名")
    parser.add_argument("-ff", "--filelist-filename", type=str, help="yaml模板列表文件名")
    parser.add_argument("-b", "--batch", nargs="+", type=str, help="批处理配置文件（参数列表）")
    args = parser.parse_args()
    return args


def main(batch, **kwargs):
    if batch:
        for b in batch:
            for data in configlib.load(b):
                Core(**data).run()
    else:
        Core(**kwargs).run()


if __name__ == "__main__":
    # 参数选项
    args = get_args()
    main(**vars(args))
