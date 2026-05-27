from __future__ import annotations

import re
import shutil
import tempfile
from collections.abc import Mapping
from pathlib import Path

from configlib import load_config

_BUNDLE_MARKER = re.compile(
    r"^\s*#\s*([\w./\\-]+\.(?:ya?ml|json5?|toml))\s*$",
    re.IGNORECASE,
)
_INCLUDE_REF = re.compile(r"!include\s+(\S+)")


def is_config_bundle_text(text: str) -> bool:
    """首条非空行是否为 ``#<文件名>`` 分段标记。"""
    for line in text.splitlines():
        if not line.strip():
            continue
        return _BUNDLE_MARKER.match(line) is not None
    return False


def parse_config_bundle(text: str) -> list[tuple[str, str]]:
    """按 ``# 文件名`` 拆成有序虚拟文件列表。"""
    sections: list[tuple[str, str]] = []
    current_name: str | None = None
    current_lines: list[str] = []

    for line in text.splitlines(keepends=True):
        marker = _BUNDLE_MARKER.match(line.rstrip("\r\n"))
        if marker:
            if current_name is not None:
                sections.append((current_name, "".join(current_lines)))
            current_name = marker.group(1)
            current_lines = []
            continue
        if current_name is None:
            if line.strip():
                raise ValueError("捆绑配置须以 #<文件名> 分段标记开头")
            continue
        current_lines.append(line)

    if current_name is None:
        return []

    sections.append((current_name, "".join(current_lines)))
    return sections


def _collect_include_refs(sections: list[tuple[str, str]]) -> set[str]:
    refs: set[str] = set()
    for _, content in sections:
        for match in _INCLUDE_REF.finditer(content):
            refs.add(match.group(1).replace("\\", "/"))
    return refs


def _normalize_section_name(name: str) -> str:
    return name.replace("\\", "/")


def load_bundle_config(path: Path) -> dict[str, object] | None:
    """加载 ``# 文件名`` 多段捆绑配置；非捆绑文件返回 ``None``。"""
    text = path.read_text(encoding="utf-8")
    if not is_config_bundle_text(text):
        return None

    sections = parse_config_bundle(text)
    if not sections:
        return None

    seen: set[str] = set()
    for name, _ in sections:
        norm = _normalize_section_name(name)
        if norm in seen:
            raise ValueError(f"捆绑配置中重复的文件名: {name!r}")
        seen.add(norm)

    bundle_dir = path.parent.resolve()
    include_refs = _collect_include_refs(sections)

    with tempfile.TemporaryDirectory(prefix="jinja_build_cfg_") as tmp:
        root = Path(tmp)
        for name, content in sections:
            dest = root / _normalize_section_name(name)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")

        for rel in include_refs:
            norm = _normalize_section_name(rel)
            if (root / norm).exists():
                continue
            external = (bundle_dir / rel).resolve()
            if not external.is_file():
                continue
            dest = root / norm
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(external, dest)

        entry = root / _normalize_section_name(sections[0][0])
        loaded = load_config(entry)
        if loaded is None:
            return {}
        if isinstance(loaded, Mapping):
            return dict(loaded)
        raise TypeError(
            f"捆绑配置入口 {sections[0][0]!r} 须解析为 mapping，"
            f"实际为 {type(loaded).__name__}"
        )


__all__ = [
    "is_config_bundle_text",
    "load_bundle_config",
    "parse_config_bundle",
]
