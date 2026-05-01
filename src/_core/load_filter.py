import os
from pathlib import Path
from _utils import jinja
from typing import List, Callable, Dict


def load_filter(filter_list: List[str]) -> Dict[str, Callable]:
    '''
    filter_list : filter文件/目录的列表
    '''
    paths = [x for path in filter_list for x in search_python(path)]
    return {path.stem: jinja.load_filter(path)[0] for path in paths}


def search_python(file_path: str) -> List[Path]:
    path = Path(file_path)
    if path.is_file():
        return [path]
    elif path.is_dir():
        return path.rglob("*.py")
