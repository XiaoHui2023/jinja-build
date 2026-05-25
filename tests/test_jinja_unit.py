import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from _utils import _filters, _jinja  # noqa: E402
from _utils._dynamic_loading import get_definitions_in_order, load_module  # noqa: E402


class ToDictTests(unittest.TestCase):
    def test_pydantic_merges_property_without_overwriting_fields(self) -> None:
        class M(BaseModel):
            name: str
            score: int = 1

            @property
            def label(self) -> str:
                return self.name.upper()

        data = _jinja.to_dict(M(name="x", score=2))
        self.assertEqual(data["name"], "x")
        self.assertEqual(data["score"], 2)
        self.assertEqual(data["label"], "X")

    def test_dataclass_merges_property(self) -> None:
        @dataclass
        class Row:
            key: str

            @property
            def doubled(self) -> str:
                return self.key * 2

        self.assertEqual(_jinja.to_dict(Row("ab"))["doubled"], "abab")

    def test_nested_structures(self) -> None:
        payload = {"items": [{"n": 1}, {"n": 2}], "tags": ("a", "b")}
        self.assertEqual(_jinja.to_dict(payload)["items"][1]["n"], 2)


class FilterTests(unittest.TestCase):
    def test_builtin_replace_and_join(self) -> None:
        env = _jinja.get_env("x.j2", [], {})
        render = env.from_string("{{ 'ab' | replace('a','z') }}|{{ '-' | join(['x','y']) }}")
        self.assertEqual(render.render({}), "zb|x-y")

    def test_model_method_filter_binds_instance(self) -> None:
        class M:
            def __init__(self, v: str) -> None:
                self.v = v

            def tag(self, prefix: str) -> str:
                return f"{prefix}:{self.v}"

        inst = M("ok")
        flt = _filters.build_model_method_filters(M, inst)["tag"]
        self.assertEqual(flt("", "p"), "p:ok")

    def test_private_methods_are_not_filters(self) -> None:
        class M:
            def _hidden(self) -> str:
                return "x"

            def visible(self) -> str:
                return "y"

        names = set(_filters.build_model_method_filters(M, M()).keys())
        self.assertEqual(names, {"visible"})


class LoadModelsTests(unittest.TestCase):
    def test_multiple_classes_keep_source_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "models.py"
            path.write_text(
                "class Alpha:\n    pass\n\nclass Beta:\n    pass\n\nclass Data:\n"
                "    def __init__(self, name=''):\n        self.name = name\n",
                encoding="utf-8",
            )
            names = [c.__name__ for c in _jinja.load_models(path)]
            self.assertEqual(names, ["Alpha", "Beta", "Data"])

    def test_definitions_in_order_includes_functions_and_assignments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "m.py"
            path.write_text(
                "FLAG = 1\n"
                "def fn():\n    pass\n"
                "class C:\n    pass\n",
                encoding="utf-8",
            )
            self.assertEqual(get_definitions_in_order(path), ["FLAG", "fn", "C"])


class JinjaBuiltinFilterCoexistenceTests(unittest.TestCase):
    def test_jinja_sum_filter_with_attribute_still_works(self) -> None:
        env = _jinja.get_env("t.j2", [], {})
        tpl = env.from_string("{{ items | map(attribute='qty') | sum }}")
        out = tpl.render({"items": [{"qty": 2}, {"qty": 3}]})
        self.assertEqual(out, "5")


class RenderEnvironmentTests(unittest.TestCase):
    def test_strict_undefined_raises(self) -> None:
        env = _jinja.get_env(__file__, [], {})
        tpl = env.from_string("{{ missing }}")
        with self.assertRaises(Exception):
            tpl.render({})

    def test_safe_dict_environment_prefers_keys(self) -> None:
        from jinja2 import FileSystemLoader

        env = _jinja.SafeDictEnvironment(loader=FileSystemLoader([Path(__file__).parent]))
        tpl = env.from_string("{{ data.items }}")
        self.assertEqual(tpl.render({"data": {"items": [1]}}), "[1]")


if __name__ == "__main__":
    unittest.main()
