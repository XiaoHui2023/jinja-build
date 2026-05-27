"""测试用临时模板工程辅助。"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from _core import Core  # noqa: E402


class TemplateProject:
    """在临时目录搭建最小可运行的模板仓库并执行 Core。"""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.template = root / "template"
        self.output = root / "output"
        self.template.mkdir(parents=True, exist_ok=True)

    def write_models(self, source: str) -> None:
        (self.template / "models.py").write_text(source, encoding="utf-8")

    def write_json(self, name: str, data: dict[str, Any]) -> Path:
        path = self.root / name
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def write_yaml(self, name: str, text: str) -> Path:
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path

    def write_template(self, rel: str, text: str) -> Path:
        path = self.template / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def run(
        self,
        *,
        input_path: str | None = None,
        batch: list[str] | None = None,
        output: str | None = None,
        models_filename: str = "models.py",
        template: str | None = None,
        **kwargs: object,
    ) -> None:
        Core(
            template=template or str(self.template),
            input=input_path,
            batch=batch,
            output=output or str(self.output),
            models_filename=models_filename,
            **kwargs,
        ).run()

    def read_output(self, rel: str) -> str:
        return (self.output / rel).read_text(encoding="utf-8")

    def read_output_text(self, rel: str) -> str:
        """读取输出并去掉末尾换行，便于断言。"""
        return self.read_output(rel).rstrip("\n")

    def output_exists(self, rel: str) -> bool:
        return (self.output / rel).exists()

    def output_is_empty(self) -> bool:
        if not self.output.exists():
            return True
        return not any(self.output.iterdir())
