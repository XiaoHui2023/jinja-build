import logging
import time
from pathlib import Path

from pydantic import BaseModel, Field, PrivateAttr

from ._fingerprint import directory_fingerprint
from ._loading import load_ordered_objects
from ._markdown import render_markdown, repo_display_name
from ._repo import Repository, discover_repositories
from .schema import collect_schemas

Snapshot = tuple[tuple[str, int, int], ...]


class Doc(BaseModel):
    """扫描模板仓库，把数据结构文件生成可读文档。"""

    template: str = Field(description="要扫描的模板根目录。")
    output: str = Field(description="文档输出根目录。")
    models_filename: str = Field(default="models.py", description="用于识别仓库的数据结构文件名。")
    interval: float = Field(default=1.0, description="持续监听时检查目录变化的间隔秒数。")

    _last_snapshots: dict[Path, Snapshot] = PrivateAttr(default_factory=dict)
    _failed_snapshots: dict[Path, Snapshot] = PrivateAttr(default_factory=dict)

    def run(self) -> None:
        """持续监听模板目录，发现变化后更新对应文档。"""
        logging.info("开始监听模板目录：%s", self.template)
        while True:
            self.run_once()
            time.sleep(self.interval)

    def run_once(self) -> None:
        """扫描一次模板目录，并渲染发生变化的仓库。"""
        for repo in discover_repositories(self.template, self.models_filename):
            self._render_if_needed(repo)

    def _render_if_needed(self, repo: Repository) -> None:
        """按仓库状态决定是否需要生成文档。"""
        snapshot = self._snapshot(repo)
        if self._failed_snapshots.get(repo.root) == snapshot:
            return
        if self._last_snapshots.get(repo.root) == snapshot:
            return

        try:
            final_snapshot = self._render_until_stable(repo)
        except Exception as error:
            self._failed_snapshots[repo.root] = snapshot
            output_path = repo.output_path(Path(self.output))
            logging.exception("文档生成失败：%s；原因：%s", output_path, error)
            return

        self._failed_snapshots.pop(repo.root, None)
        self._last_snapshots[repo.root] = final_snapshot

    def _render_until_stable(self, repo: Repository) -> Snapshot:
        """渲染后再检查一次变化，必要时继续补渲染。"""
        while True:
            before = self._snapshot(repo)
            self._render_one(repo)
            after = self._snapshot(repo)
            if after == before:
                return after
            logging.info("渲染期间发现变化，重新生成：%s", repo.root)

    def _render_one(self, repo: Repository) -> None:
        """读取一个仓库的数据结构并写出 Markdown。"""
        objects = load_ordered_objects(repo.models_path)
        schemas = collect_schemas(objects)
        content = render_markdown(
            repo_display_name(repo.relative_path, repo.root),
            schemas,
        )
        output_path = repo.output_path(Path(self.output))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        logging.info("文档已生成：%s", output_path)

    def _snapshot(self, repo: Repository) -> Snapshot:
        """读取仓库当前输入文件状态。"""
        return directory_fingerprint(repo.root, ignored_root=Path(self.output))


__all__ = [
    "Doc",
]
