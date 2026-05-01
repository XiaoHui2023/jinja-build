from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Repository:
    """代表一个带数据结构文件的模板仓库。"""

    root: Path
    """仓库目录"""
    models_path: Path
    """仓库里的数据结构文件"""
    relative_path: Path
    """仓库相对模板根目录的位置"""

    def output_path(self, output_root: Path) -> Path:
        """计算这个仓库的文档输出位置。"""
        if str(self.relative_path) == ".":
            return output_root / f"{self.root.name}.md"
        return output_root / self.relative_path.with_suffix(".md")


def discover_repositories(template_root: str | Path, models_filename: str) -> list[Repository]:
    """递归发现仓库，进入仓库后不再继续找子仓库。"""
    root = Path(template_root)
    if not root.exists():
        raise FileNotFoundError(root)
    if not root.is_dir():
        raise NotADirectoryError(root)
    return list(_walk(root, root, models_filename))


def _walk(current: Path, template_root: Path, models_filename: str) -> list[Repository]:
    """从当前目录向下寻找仓库根。"""
    models_path = current / models_filename
    if models_path.exists():
        return [
            Repository(
                root=current,
                models_path=models_path,
                relative_path=current.relative_to(template_root),
            )
        ]

    repos = []
    for child in sorted(current.iterdir(), key=lambda item: item.name):
        if child.is_dir():
            repos.extend(_walk(child, template_root, models_filename))
    return repos
