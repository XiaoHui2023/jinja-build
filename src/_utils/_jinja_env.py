from collections.abc import Callable
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from ._filters import build_builtin_filters
from ._jinja_view import TemplateStrictUndefined, TemplateView


class SafeDictEnvironment(Environment):
    """让模板读取字典时优先按键名取值；模型走 TemplateView 解析。"""

    def getattr(self, obj: object, attribute: str) -> object:
        """读取模板里的属性访问。"""
        if isinstance(obj, TemplateView):
            try:
                return obj.get_attribute(attribute)
            except AttributeError:
                return self.undefined(obj=obj, name=attribute)
        if isinstance(obj, dict) and attribute in obj:
            return obj[attribute]
        return super().getattr(obj, attribute)

    def getitem(self, obj: object, argument: object) -> object:
        """读取模板里的下标访问。"""
        if isinstance(obj, TemplateView):
            try:
                return obj.get_item(argument)
            except KeyError:
                return self.undefined(obj=obj, name=argument)
        return super().getitem(obj, argument)


def resolve_template_name(file_path: Path, search_paths: list[str | Path]) -> str:
    """把磁盘上的模板路径解析为 loader 可用的相对名。"""
    resolved = file_path.resolve()
    roots: list[Path] = []
    seen: set[Path] = set()
    for root in [*search_paths, resolved.parent]:
        root = Path(root).resolve()
        if root in seen:
            continue
        seen.add(root)
        roots.append(root)

    best: str | None = None
    best_depth = -1
    for root in roots:
        try:
            rel = resolved.relative_to(root)
        except ValueError:
            continue
        depth = len(rel.parts)
        if depth > best_depth:
            best_depth = depth
            best = rel.as_posix()

    return best if best is not None else resolved.name


def get_env(
    file_path: str | Path,
    search_paths: list[str | Path],
    globals_var: dict[str, object],
    filters_var: dict[str, Callable[..., object]] | None = None,
) -> SafeDictEnvironment:
    """创建单个模板文件使用的渲染环境。"""
    current_dir = Path(file_path).parent.resolve()
    loader_roots = [Path(p).resolve() for p in search_paths]
    if current_dir not in loader_roots:
        loader_roots.append(current_dir)

    env = SafeDictEnvironment(
        undefined=TemplateStrictUndefined,
        loader=FileSystemLoader([str(p) for p in loader_roots]),
        lstrip_blocks=True,
        extensions=[
            "jinja2.ext.do",
            "jinja2.ext.loopcontrols",
        ],
    )

    var_map = BASE_GLOBALS | globals_var
    env.globals.update(var_map)
    env.filters.update(build_builtin_filters())
    if filters_var:
        env.filters.update(filters_var)

    return env


BASE_GLOBALS: dict[str, object] = {
    "len": len,
}


__all__ = [
    "BASE_GLOBALS",
    "SafeDictEnvironment",
    "get_env",
    "resolve_template_name",
]
