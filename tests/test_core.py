import json
import sys
import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from _core import Core  # noqa: E402
from _utils._dynamic_loading import load_module  # noqa: E402


class CoreRenderTests(unittest.TestCase):
    """覆盖模板渲染、批处理和动态加载的关键行为。"""

    def test_template_directory_input_config_and_models_render_together(self) -> None:
        """模板目录、输入配置和数据结构文件会一起完成真实渲染。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template"
            output = root / "output"
            reports = template / "reports"
            config = template / "config"
            reports.mkdir(parents=True)
            config.mkdir(parents=True)
            self._write_real_model(template)
            self._write_json(
                root / "project.json",
                {
                    "project": "jinja-build",
                    "owner": "tools",
                    "items": [
                        {"name": "cli", "count": 2},
                        {"name": "server", "count": 3},
                    ],
                },
            )
            (reports / "summary.md.j2").write_text(
                "# {{ project }}\n"
                "Owner: {{ owner }}\n"
                "Title: {{ title() }}\n"
                "Total: {{ total() }}\n"
                "{% for item in items -%}\n"
                "- {{ item.name }} x{{ item.count }}\n"
                "{% endfor %}\n",
                encoding="utf-8",
            )
            (config / "app.conf.j2").write_text(
                "name={{ project }}\n"
                "owner={{ owner }}\n"
                "item_count={{ len(items) }}\n",
                encoding="utf-8",
            )

            Core(
                template=str(template),
                input=str(root / "project.json"),
                output=str(output),
            ).run()

            self.assertEqual(
                (output / "reports" / "summary.md").read_text(encoding="utf-8"),
                "# jinja-build\n"
                "Owner: tools\n"
                "Title: JINJA-BUILD/tools\n"
                "Total: 5\n"
                "- cli x2\n"
                "- server x3\n",
            )
            self.assertEqual(
                (output / "config" / "app.conf").read_text(encoding="utf-8"),
                "name=jinja-build\n"
                "owner=tools\n"
                "item_count=2",
            )

    def test_single_render_writes_non_empty_output(self) -> None:
        """单个输入会渲染所有非空模板。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template"
            output = root / "output"
            template.mkdir()
            self._write_model(template)
            self._write_json(root / "ada.json", {"name": "Ada"})
            (template / "hello.txt.j2").write_text(
                "Hello {{ name }} {{ title() }}",
                encoding="utf-8",
            )

            Core(
                template=str(template),
                input=str(root / "ada.json"),
                output=str(output),
            ).run()

            self.assertEqual((output / "hello.txt").read_text(encoding="utf-8"), "Hello Ada ADA")

    def test_blank_output_skips_file_and_directory(self) -> None:
        """空白渲染结果不会创建文件，也不会顺带创建空目录。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template"
            output = root / "output"
            nested = template / "nested"
            nested.mkdir(parents=True)
            self._write_model(template)
            (nested / "empty.txt.j2").write_text("   \n\n", encoding="utf-8")

            Core(template=str(template), output=str(output)).run()

            self.assertFalse((output / "nested").exists())
            self.assertFalse((output / "nested" / "empty.txt").exists())

    def test_batch_outputs_use_input_stems(self) -> None:
        """批处理会把每个输入输出到同名子目录。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template"
            output = root / "output"
            template.mkdir()
            self._write_model(template)
            self._write_json(root / "dev.json", {"name": "dev"})
            self._write_json(root / "prod.json", {"name": "prod"})
            (template / "name.txt.j2").write_text("{{ title() }}", encoding="utf-8")

            Core(
                template=str(template),
                batch=[str(root / "dev.json"), str(root / "prod.json")],
                output=str(output),
            ).run()

            self.assertEqual((output / "dev" / "name.txt").read_text(encoding="utf-8"), "DEV")
            self.assertEqual((output / "prod" / "name.txt").read_text(encoding="utf-8"), "PROD")

    def test_batch_rejects_duplicate_output_names(self) -> None:
        """批处理输入文件名重复时会提前失败。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template"
            left = root / "left"
            right = root / "right"
            template.mkdir()
            left.mkdir()
            right.mkdir()
            self._write_model(template)
            self._write_json(left / "same.json", {"name": "left"})
            self._write_json(right / "same.json", {"name": "right"})

            with self.assertRaises(ValidationError) as error:
                Core(
                    template=str(template),
                    batch=[str(left / "same.json"), str(right / "same.json")],
                    output=str(root / "output"),
                )

            self.assertIn("Duplicate batch output name: same", str(error.exception))

    def test_property_and_filters_are_available_in_templates(self) -> None:
        """property 作变量、内置与 models 方法作过滤器。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template"
            output = root / "output"
            template.mkdir()
            (template / "models.py").write_text(
                "class Data:\n"
                "    def __init__(self, name=''):\n"
                "        self.name = name\n"
                "\n"
                "    @property\n"
                "    def label(self):\n"
                "        return self.name.upper()\n"
                "\n"
                "    def title(self):\n"
                "        return f'title:{self.name}'\n",
                encoding="utf-8",
            )
            self._write_json(root / "ada.json", {"name": "ada"})
            (template / "out.txt.j2").write_text(
                "{{ label }}|{{ name | replace('a', 'o') }}|{{ '' | title }}\n"
                "{% set items = [1, 2, 3] %}{{ items | len }}|{{ items | sum }}\n",
                encoding="utf-8",
            )

            Core(
                template=str(template),
                input=str(root / "ada.json"),
                output=str(output),
            ).run()

            self.assertEqual(
                (output / "out.txt").read_text(encoding="utf-8"),
                "ADA|odo|title:ada\n3|6",
            )

    def test_dynamic_loading_restores_sys_path(self) -> None:
        """动态导入期间可读同目录辅助文件，结束后恢复搜索路径。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "helper.py").write_text("VALUE = 3\n", encoding="utf-8")
            model_file = root / "models.py"
            model_file.write_text(
                "from helper import VALUE\n"
                "class Model:\n"
                "    x = VALUE\n",
                encoding="utf-8",
            )
            before = sys.path.copy()

            attrs = load_module(model_file)

            self.assertEqual(attrs["Model"].x, 3)
            self.assertEqual(sys.path, before)
            self.assertTrue(attrs["Model"].__module__.startswith("_jinja_build_dynamic_models_"))

    def _write_model(self, template: Path) -> None:
        """写入测试用的数据结构文件。"""
        (template / "models.py").write_text(
            "class Data:\n"
            "    def __init__(self, name=''):\n"
            "        self.name = name\n"
            "\n"
            "    def title(self):\n"
            "        return self.name.upper()\n",
            encoding="utf-8",
        )

    def _write_real_model(self, template: Path) -> None:
        """写入端到端渲染测试使用的数据结构文件。"""
        (template / "models.py").write_text(
            "from pydantic import BaseModel\n"
            "\n"
            "class Item(BaseModel):\n"
            "    name: str\n"
            "    count: int\n"
            "\n"
            "class Data(BaseModel):\n"
            "    project: str\n"
            "    owner: str\n"
            "    items: list[Item]\n"
            "\n"
            "    def title(self):\n"
            "        return f'{self.project.upper()}/{self.owner}'\n"
            "\n"
            "    def total(self):\n"
            "        return sum(item.count for item in self.items)\n",
            encoding="utf-8",
        )

    def _write_json(self, path: Path, data: dict[str, object]) -> None:
        """写入测试用输入配置。"""
        path.write_text(json.dumps(data), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
