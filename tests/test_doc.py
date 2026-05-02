import logging
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "doc"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from _doc import Doc  # noqa: E402
from _doc._logging import configure_logging  # noqa: E402
from _doc._repo import discover_repositories  # noqa: E402


class DocGenerationTests(unittest.TestCase):
    """覆盖仓库发现、结构文档和错误隔离。"""

    def test_discover_repositories_stops_at_first_models_file(self) -> None:
        """发现仓库后不会继续把子目录当成新仓库。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "a" / "b"
            nested = repo / "c"
            nested.mkdir(parents=True)
            (repo / "models.py").write_text("class Root:\n    pass\n", encoding="utf-8")
            (nested / "models.py").write_text("class Nested:\n    pass\n", encoding="utf-8")

            repos = discover_repositories(root, "models.py")

            self.assertEqual([item.relative_path.as_posix() for item in repos], ["a/b"])

    def test_run_once_writes_pydantic_and_dataclass_docs(self) -> None:
        """单次扫描会生成可读的数据结构文档。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template"
            output = root / "docs"
            repo = template / "a" / "b" / "c"
            repo.mkdir(parents=True)
            (repo / "models.py").write_text(
                textwrap.dedent(
                    '''
                    from dataclasses import dataclass
                    from pydantic import BaseModel, Field


                    class User(BaseModel):
                        """用户资料。"""

                        name: str = Field(description="用户显示名")
                        age: int = Field(default=18, description="年龄")


                    @dataclass
                    class Group:
                        """用户分组。"""

                        title: str
                        """分组名称"""
                    '''
                ),
                encoding="utf-8",
            )

            Doc(template=str(template), output=str(output)).run_once()

            content = (output / "a" / "b" / "c.md").read_text(encoding="utf-8")
            self.assertIn("# a/b/c 数据结构", content)
            self.assertIn("| name | str | 是 |  | 用户显示名 |", content)
            self.assertIn("| age | int | 否 | 18 | 年龄 |", content)
            self.assertIn("| title | str | 是 |  | 分组名称 |", content)

    def test_failed_repository_does_not_block_other_repositories(self) -> None:
        """坏仓库不会影响其他仓库输出。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template"
            output = root / "docs"
            bad = template / "bad"
            good = template / "good"
            bad.mkdir(parents=True)
            good.mkdir(parents=True)
            (bad / "models.py").write_text("raise RuntimeError('broken')\n", encoding="utf-8")
            (good / "models.py").write_text(
                "from pydantic import BaseModel, Field\n"
                "class Good(BaseModel):\n"
                "    name: str = Field(description='名称')\n",
                encoding="utf-8",
            )

            Doc(template=str(template), output=str(output)).run_once()

            self.assertFalse((output / "bad.md").exists())
            self.assertTrue((output / "good.md").exists())

    def test_failed_repository_waits_until_it_changes(self) -> None:
        """失败仓库内容不变时不会重复渲染。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template"
            output = root / "docs"
            repo = template / "bad"
            repo.mkdir(parents=True)
            models = repo / "models.py"
            models.write_text("raise RuntimeError('broken')\n", encoding="utf-8")
            doc = Doc(template=str(template), output=str(output))

            with self.assertLogs(level="ERROR") as first:
                doc.run_once()
            with self.assertNoLogs(level="ERROR"):
                doc.run_once()

            models.write_text(
                "from pydantic import BaseModel, Field\n"
                "class Fixed(BaseModel):\n"
                "    name: str = Field(description='名称')\n",
                encoding="utf-8",
            )
            doc.run_once()

            self.assertEqual(len(first.records), 1)
            self.assertTrue((output / "bad.md").exists())

    def test_configure_logging_writes_time_named_file(self) -> None:
        """日志会写入日期和时间命名的文件。"""
        with tempfile.TemporaryDirectory() as tmp:
            try:
                log_path = configure_logging(tmp)
                logging.info("hello doc")
            finally:
                for handler in logging.getLogger().handlers:
                    handler.close()
                logging.getLogger().handlers.clear()

            self.assertEqual(log_path.parent.parent, Path(tmp))
            self.assertRegex(log_path.parent.name, r"^\d{4}-\d{2}-\d{2}$")
            self.assertRegex(log_path.stem, r"^\d{2}-\d{2}-\d{2}$")
            self.assertEqual(log_path.suffix, ".log")
            self.assertIn("hello doc", log_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
