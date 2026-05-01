import yaml
import json
from typing import Dict
from _utils import YAML
from pathlib import Path


def load_input(src: str) -> Dict:
    """
    加载不同类型的输入文件

    支持:
        json
        yaml
    """
    path = Path(src)
    suffix = path.suffix.lower()
    suffix_json = [".json"]
    suffix_yaml = [".yaml", ".yml"]
    suffix_all = suffix_json + suffix_yaml

    if suffix in suffix_json:
        return load_json(path)
    elif suffix in suffix_yaml:
        return load_yaml(path)
    else:
        raise Exception(f"Unsupport suffix: '{suffix}'. require {suffix_all}")


def load_json(src: str) -> dict:
    with open(src, "r", encoding="utf-8") as f:
        return json.load(f)


def load_yaml(src: str, data=None) -> dict:
    return YAML.load(src, data)
