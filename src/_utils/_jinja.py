import inspect
from collections.abc import Callable
from pathlib import Path
from typing import Any

from jinja2.exceptions import TemplateError

from ._dynamic_loading import load_module
from ._jinja_convert import to_dict
from ._jinja_env import SafeDictEnvironment, get_env, resolve_template_name
from ._cli_user_error import raise_after_report
from ._jinja_errors import print_render_user_error, print_template_error
from ._jinja_view import build_render_context


def _handle_render_error(
    exc: BaseException,
    *,
    entry_path: Path,
    defer_error_report: bool,
) -> None:
    if defer_error_report:
        raise exc
    if isinstance(exc, TemplateError):
        print_template_error(exc, entry_path=entry_path)
    else:
        print_render_user_error(exc, entry_path=entry_path)
    raise_after_report(exc)


def render(
    src: str | Path,
    data: Any,
    globals_var: dict[str, object] | None = None,
    filters_var: dict[str, Callable[..., object]] | None = None,
    search_paths: list[str | Path] | None = None,
    *,
    defer_error_report: bool = False,
) -> str:
    """渲染模板文件。

    Args:
        src: 模板文件路径
        data: 输入数据对象
        globals_var: 模板里可直接调用的对象
        filters_var: 模板管道过滤器
        search_paths: 模板继承和包含时可搜索的目录
        defer_error_report: 为 True 时不打印错误卡片，由调用方统一展示
    """
    if globals_var is None:
        globals_var = {}
    if filters_var is None:
        filters_var = {}
    if search_paths is None:
        search_paths = []

    try:
        context = build_render_context(data)
    except Exception as exc:
        _handle_render_error(
            exc,
            entry_path=Path(src).resolve(),
            defer_error_report=defer_error_report,
        )

    return render_context(
        src,
        context,
        globals_var,
        filters_var=filters_var,
        search_paths=search_paths,
        defer_error_report=defer_error_report,
    )


def render_context(
    src: str | Path,
    context: dict[str, Any],
    globals_var: dict[str, object] | None = None,
    filters_var: dict[str, Callable[..., object]] | None = None,
    search_paths: list[str | Path] | None = None,
    *,
    defer_error_report: bool = False,
) -> str:
    """用已构造的模板上下文渲染模板文件。"""
    if globals_var is None:
        globals_var = {}
    if filters_var is None:
        filters_var = {}
    if search_paths is None:
        search_paths = []

    src_path = Path(src).resolve()
    env = get_env(src_path, search_paths, globals_var, filters_var)
    template_name = resolve_template_name(src_path, search_paths)

    try:
        template = env.get_template(template_name)
    except TemplateError as exc:
        _handle_render_error(exc, entry_path=src_path, defer_error_report=defer_error_report)

    try:
        return template.render(context)
    except TemplateError as exc:
        _handle_render_error(exc, entry_path=src_path, defer_error_report=defer_error_report)
    except Exception as exc:
        _handle_render_error(exc, entry_path=src_path, defer_error_report=defer_error_report)


def load_models(file_path: str | Path) -> list[type]:
    """从数据结构文件读取可用类型。

    Args:
        file_path: 数据结构文件路径
    """
    attrs = load_module(file_path)
    cls_map = {name: x for name, x in attrs.items() if inspect.isclass(x)}

    if len(cls_map) == 0:
        raise Exception(f"Not found class in '{file_path}'")

    return list(cls_map.values())


__all__ = [
    "SafeDictEnvironment",
    "build_render_context",
    "get_env",
    "load_models",
    "render",
    "render_context",
    "resolve_template_name",
    "to_dict",
]
