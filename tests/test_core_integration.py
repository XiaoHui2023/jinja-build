import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from _core import Core  # noqa: E402

from _case import TemplateProject  # noqa: E402


class CoreValidationTests(unittest.TestCase):
    def test_input_and_batch_are_mutually_exclusive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = TemplateProject(Path(tmp))
            p.write_models("class Data:\n    def __init__(self, name=''):\n        self.name = name\n")
            with self.assertRaises(ValidationError):
                Core(
                    template=str(p.template),
                    input=str(p.write_json("a.json", {"name": "a"})),
                    batch=[str(p.write_json("b.json", {"name": "b"}))],
                    output=str(p.output),
                )

    def test_missing_models_file_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = TemplateProject(Path(tmp))
            with self.assertRaises(FileNotFoundError):
                Core(template=str(p.template), output=str(p.output)).run()

    def test_models_without_class_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = TemplateProject(Path(tmp))
            (p.template / "models.py").write_text("FLAG = 1\n", encoding="utf-8")
            with self.assertRaises(Exception) as ctx:
                Core(template=str(p.template), output=str(p.output)).run()
            self.assertIn("Not found class", str(ctx.exception))


class SingleTemplateFileTests(unittest.TestCase):
    def test_single_j2_file_writes_to_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tpl = root / "only.j2"
            out = root / "result.txt"
            tpl.write_text("v={{ name }}\n", encoding="utf-8")
            (root / "models.py").write_text(
                "class Data:\n    def __init__(self, name=''):\n        self.name = name\n",
                encoding="utf-8",
            )
            (root / "in.json").write_text('{"name": "solo"}', encoding="utf-8")
            Core(template=str(tpl), input=str(root / "in.json"), output=str(out)).run()
            self.assertEqual(out.read_text(encoding="utf-8").rstrip("\n"), "v=solo")


class ConfigAndModelsTests(unittest.TestCase):
    def test_yaml_config_variable_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = TemplateProject(Path(tmp))
            p.write_models(
                textwrap.dedent(
                    """
                    from pydantic import BaseModel


                    class Data(BaseModel):
                        project_name: str
                        file_count: int
                    """
                )
            )
            p.write_yaml(
                "cfg.yaml",
                "vars:\n  prefix: acme\n  n: 2\n"
                "project_name: ${vars.prefix}-app\n"
                "file_count: ${vars.n}\n",
            )
            p.write_template("out.txt.j2", "{{ project_name }}|{{ file_count }}\n")
            p.run(input_path=str(p.root / "cfg.yaml"))
            self.assertEqual(p.read_output_text("out.txt"), "acme-app|2")

    def test_empty_input_uses_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = TemplateProject(Path(tmp))
            p.write_models(
                "class Data:\n"
                "    def __init__(self, name='default'):\n"
                "        self.name = name\n"
            )
            p.write_template("x.txt.j2", "{{ name }}\n")
            p.run()
            self.assertEqual(p.read_output_text("x.txt"), "default")

    def test_custom_models_filename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = TemplateProject(Path(tmp))
            (p.template / "schema.py").write_text(
                "class Data:\n    def __init__(self, v='ok'):\n        self.v = v\n",
                encoding="utf-8",
            )
            p.write_template("t.txt.j2", "{{ v }}\n")
            Core(
                template=str(p.template),
                output=str(p.output),
                models_filename="schema.py",
            ).run()
            self.assertEqual(p.read_output_text("t.txt"), "ok")


class GlobalsFiltersAndModelsTests(unittest.TestCase):
    def test_multiple_model_classes_expose_types_and_last_class_methods(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = TemplateProject(Path(tmp))
            p.write_models(
                textwrap.dedent(
                    """
                    class Prefix:
                        @staticmethod
                        def tag():
                            return "P"

                    class Data:
                        def __init__(self, name=""):
                            self.name = name

                        def title(self):
                            return self.name.upper()
                    """
                )
            )
            p.write_json("in.json", {"name": "mix"})
            p.write_template(
                "combo.txt.j2",
                "cls={{ Prefix.tag() }}|fn={{ title() }}|flt={{ '' | title }}\n",
            )
            p.run(input_path=str(p.root / "in.json"))
            self.assertEqual(p.read_output_text("combo.txt"), "cls=P|fn=MIX|flt=MIX")

    def test_package_absolute_import_in_models(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = TemplateProject(Path(tmp))
            lib = p.template / "demo_lib"
            lib.mkdir()
            (lib / "__init__.py").write_text("", encoding="utf-8")
            (lib / "fmt.py").write_text(
                "def slug(text: str) -> str:\n    return text.replace(' ', '-')\n",
                encoding="utf-8",
            )
            p.write_models(
                "from demo_lib.fmt import slug\n\n"
                "class Data:\n"
                "    def __init__(self, name=''):\n"
                "        self.name = name\n"
                "    def path(self):\n"
                "        return slug(self.name)\n"
            )
            p.write_json("in.json", {"name": "a b"})
            p.write_template("o.txt.j2", "{{ path() }}|{{ '' | path }}\n")
            p.run(input_path=str(p.root / "in.json"))
            self.assertEqual(p.read_output_text("o.txt"), "a-b|a-b")


class TemplateFeatureCombinationTests(unittest.TestCase):
    def test_macro_extends_include_in_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = TemplateProject(Path(tmp))
            p.write_models(
                "class Data:\n    def __init__(self, title=''):\n        self.title = title\n"
            )
            p.write_json("in.json", {"title": "T"})
            p.write_template("_macros.j2", "{% macro h(t) %}[{{ t }}]{% endmacro %}\n")
            p.write_template("layout.j2", "{% block body %}{% endblock %}\n")
            p.write_template(
                "page.j2",
                "{% extends 'layout.j2' %}{% from '_macros.j2' import h %}"
                "{% block body %}{{ h(title) }}{% include '_macros.j2' %}{% endblock %}\n",
            )
            p.run(input_path=str(p.root / "in.json"))
            self.assertIn("[T]", p.read_output("page"))

    def test_conditional_blank_and_content_mix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = TemplateProject(Path(tmp))
            p.write_models(
                textwrap.dedent(
                    """
                    class Data:
                        def __init__(self, emit_extra=False, emit_readme=True, label=""):
                            self.emit_extra = emit_extra
                            self.emit_readme = emit_readme
                            self.label = label
                    """
                )
            )
            p.write_json("in.json", {"emit_extra": False, "emit_readme": True, "label": "x"})
            p.write_template("always.txt.j2", "A={{ label }}\n")
            p.write_template(
                "readme.txt.j2",
                "{% if emit_readme %}R={{ label }}{% endif %}\n",
            )
            p.write_template(
                "skip.txt.j2",
                "{% if emit_extra %}X{% endif %}\n",
            )
            p.run(input_path=str(p.root / "in.json"))
            self.assertTrue(p.output_exists("always.txt"))
            self.assertTrue(p.output_exists("readme.txt"))
            self.assertFalse(p.output_exists("skip.txt"))

    def test_pydantic_nested_and_property_in_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = TemplateProject(Path(tmp))
            p.write_models(
                textwrap.dedent(
                    """
                    from pydantic import BaseModel


                    class Item(BaseModel):
                        name: str
                        qty: int

                    class Data(BaseModel):
                        items: list[Item]

                        @property
                        def total_qty(self) -> int:
                            return sum(i.qty for i in self.items)
                    """
                )
            )
            p.write_json(
                "in.json",
                {"items": [{"name": "a", "qty": 2}, {"name": "b", "qty": 3}]},
            )
            p.write_template(
                "sum.txt.j2",
                "{% for i in items %}{{ i.name }}:{{ i.qty }};{% endfor %}|{{ total_qty }}\n",
            )
            p.run(input_path=str(p.root / "in.json"))
            self.assertEqual(p.read_output_text("sum.txt"), "a:2;b:3;|5")


class BatchParallelCombinationTests(unittest.TestCase):
    def test_batch_times_nested_templates_with_isolated_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = TemplateProject(Path(tmp))
            p.write_models(
                "class Data:\n"
                "    def __init__(self, name=''):\n"
                "        self.name = name\n"
                "    def mark(self):\n"
                "        return self.name.upper()\n"
            )
            a = p.write_json("alpha.json", {"name": "alpha"})
            b = p.write_json("beta.json", {"name": "beta"})
            p.write_template("flat.txt.j2", "{{ mark() }}\n")
            p.write_template("deep/nested.txt.j2", "{{ name | upper }}\n")
            p.write_template("optional/empty.txt.j2", "   \n")
            p.run(batch=[str(a), str(b)])
            self.assertEqual(p.read_output_text("alpha/flat.txt"), "ALPHA")
            self.assertEqual(p.read_output_text("alpha/deep/nested.txt"), "ALPHA")
            self.assertEqual(p.read_output_text("beta/flat.txt"), "BETA")
            self.assertFalse(p.output_exists("alpha/optional/empty.txt"))
            self.assertFalse(p.output_exists("beta/optional"))

    def test_batch_three_configs_with_filter_heavy_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = TemplateProject(Path(tmp))
            p.write_models(
                textwrap.dedent(
                    """
                    class Data:
                        def __init__(self, raw="", tags=None):
                            self.raw = raw
                            self.tags = tags or []

                        @property
                        def head(self):
                            return self.raw[:2]

                        def pack(self, sep):
                            return sep.join(self.tags)
                    """
                )
            )
            paths = [
                p.write_json("one.json", {"raw": "ab", "tags": ["x"]}),
                p.write_json("two.json", {"raw": "cd", "tags": ["y", "z"]}),
                p.write_json("three.json", {"raw": "ef", "tags": []}),
            ]
            p.write_template(
                "out.txt.j2",
                "{{ head }}|{{ raw | replace('a','@') }}|{{ '' | pack(',') }}|{{ tags | len }}\n",
            )
            p.run(batch=[str(x) for x in paths])
            self.assertEqual(p.read_output_text("one/out.txt"), "ab|@b|x|1")
            self.assertEqual(p.read_output_text("two/out.txt"), "cd|cd|y,z|2")
            self.assertEqual(p.read_output_text("three/out.txt"), "ef|ef||0")


class CoreInputValidationTests(unittest.TestCase):
    def test_non_mapping_config_raises_type_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = TemplateProject(Path(tmp))
            p.write_models("class Data:\n    pass\n")
            bad = p.root / "bad.json"
            bad.write_text("[1, 2, 3]", encoding="utf-8")
            from _utils._cli_user_error import AlreadyReportedError  # noqa: E402

            with self.assertRaises(AlreadyReportedError) as ctx:
                Core(
                    template=str(p.template),
                    input=str(bad),
                    output=str(p.output),
                ).run()
            self.assertIsInstance(ctx.exception.source, TypeError)


class CoreRenderTests(unittest.TestCase):
    """保留原有用例名称空间，并补充边界组合。"""

    def test_no_templates_produces_no_output_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = TemplateProject(Path(tmp))
            p.write_models("class Data:\n    pass\n")
            p.run()
            self.assertTrue(p.output_is_empty())

    def test_whitespace_only_newlines_skips_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = TemplateProject(Path(tmp))
            p.write_models("class Data:\n    pass\n")
            p.write_template("ws.txt.j2", "\n  \n\t\n")
            p.run()
            self.assertFalse(p.output_exists("ws.txt"))


if __name__ == "__main__":
    unittest.main()
