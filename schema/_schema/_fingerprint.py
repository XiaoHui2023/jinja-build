from pathlib import Path


def directory_fingerprint(root: str | Path, ignored_root: str | Path | None = None) -> tuple[tuple[str, int, int], ...]:
    """记录目录当前文件状态，用来判断是否需要重新渲染。"""
    path = Path(root)
    ignored = Path(ignored_root).resolve() if ignored_root is not None else None
    entries = []
    for item in sorted(path.rglob("*")):
        if not item.is_file() or "__pycache__" in item.parts:
            continue
        if ignored is not None and item.resolve().is_relative_to(ignored):
            continue
        stat = item.stat()
        entries.append((item.relative_to(path).as_posix(), stat.st_mtime_ns, stat.st_size))
    return tuple(entries)
