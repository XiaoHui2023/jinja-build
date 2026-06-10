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

from jinja2.exceptions import UndefinedError  # noqa: E402

from _utils import _filters, _jinja  # noqa: E402
from _utils._cli_user_error import AlreadyReportedError  # noqa: E402
from _utils._dynamic_loading import get_definitions_in_order, load_module  # noqa: E402
from _utils._jinja_convert import to_dict  # noqa: E402
from _utils._jinja_errors import build_render_user_error_report  # noqa: E402
from _utils._jinja_view import TemplateView, resolve_attribute, wrap_for_template  # noqa: E402


class ToDictTests(unittest.TestCase):
    def test_pydantic_merges_property_without_overwriting_fields(self) -> None:
        class M(BaseModel):
            name: str
            score: int = 1

            @property
            def label(self) -> str:
                return self.name.upper()

        data = to_dict(M(name="x", score=2))
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

        self.assertEqual(to_dict(Row("ab"))["doubled"], "abab")

    def test_property_eval_error_propagates(self) -> None:
        class M(BaseModel):
            name: str

            @property
            def label(self) -> str:
                raise ValueError("prop boom")

        with self.assertRaises(RuntimeError) as ctx:
            to_dict(M(name="x"))
        self.assertIn("M.label 求值失败", str(ctx.exception))
        self.assertIsInstance(ctx.exception.__cause__, ValueError)

    def test_nested_structures(self) -> None:
        payload = {"items": [{"n": 1}, {"n": 2}], "tags": ("a", "b")}
        self.assertEqual(to_dict(payload)["items"][1]["n"], 2)


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


class TemplateViewTests(unittest.TestCase):
    def test_pydantic_field_then_alias(self) -> None:
        class User(BaseModel):
            city_name: str = Field(alias="city")

        user = User(city="bj")
        value, found = resolve_attribute(user, "city_name")
        self.assertTrue(found)
        self.assertEqual(value, "bj")
        alias_value, alias_found = resolve_attribute(user, "city")
        self.assertTrue(alias_found)
        self.assertEqual(alias_value, "bj")

    def test_property_after_fields(self) -> None:
        class Row(BaseModel):
            key: str

            @property
            def label(self) -> str:
                return self.key.upper()

        row = Row(key="ab")
        self.assertEqual(resolve_attribute(row, "label"), ("AB", True))

    def test_nested_view_keeps_path(self) -> None:
        class Inner(BaseModel):
            n: int

        class Outer(BaseModel):
            inner: Inner

        view = wrap_for_template(Outer(inner=Inner(n=3)))
        self.assertIsInstance(view, TemplateView)
        inner_view = view.get_attribute("inner")
        self.assertIsInstance(inner_view, TemplateView)
        self.assertEqual(inner_view.template_path, "root.inner")
        self.assertEqual(inner_view.get_attribute("n"), 3)

    def test_dict_key_lookup(self) -> None:
        view = wrap_for_template({"items": [{"n": 1}]})
        items = view.get_attribute("items")
        self.assertEqual(items[0].get_attribute("n"), 1)


class RenderWithTemplateViewTests(unittest.TestCase):
    def test_render_pydantic_alias_and_property(self) -> None:
        class User(BaseModel):
            city_name: str = Field(alias="city")

            @property
            def tag(self) -> str:
                return self.city_name.upper()

        class Root(BaseModel):
            user: User

        with tempfile.TemporaryDirectory() as tmp:
            tpl = Path(tmp) / "t.j2"
            tpl.write_text("{{ user.city }}|{{ user.tag }}", encoding="utf-8")
            out = _jinja.render(tpl, Root(user=User(city="bj")))
            self.assertEqual(out, "bj|BJ")

    def test_undefined_error_names_model_type(self) -> None:
        class User(BaseModel):
            name: str

        class Root(BaseModel):
            user: User

        with tempfile.TemporaryDirectory() as tmp:
            tpl = Path(tmp) / "t.j2"
            tpl.write_text("{{ user.city }}", encoding="utf-8")
            from _utils._cli_user_error import AlreadyReportedError  # noqa: E402

            try:
                _jinja.render(tpl, Root(user=User(name="x")))
            except AlreadyReportedError as wrapper:
                exc = wrapper.source
                assert isinstance(exc, UndefinedError)
                self.assertIn("User", str(exc))
                self.assertIn("city", str(exc))
                self.assertIn("缺少模板字段", str(exc))
                return
            self.fail("expected AlreadyReportedError")


class RenderUserErrorReportTests(unittest.TestCase):
    def test_user_code_site_is_collected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            models_path = Path(tmp) / "models.py"
            models_path.write_text(
                "def boom():\n    raise RuntimeError('method boom')\n",
                encoding="utf-8",
            )
            namespace: dict[str, object] = {}
            code = compile(models_path.read_text(encoding="utf-8"), str(models_path), "exec")
            exec(code, namespace)
            try:
                namespace["boom"]()
            except RuntimeError as exc:
                report = build_render_user_error_report(exc)
                self.assertEqual(report.exc_type, "RuntimeError")
                self.assertIn("method boom", report.message)
                self.assertTrue(any(site.path.resolve() == models_path.resolve() for site in report.sites))
                return
            self.fail("expected RuntimeError")


class RenderUserCodeErrorTests(unittest.TestCase):
    def test_property_error_during_context_build(self) -> None:
        class Data(BaseModel):
            name: str

            @property
            def bad(self) -> str:
                raise ValueError("prop boom")

        with tempfile.TemporaryDirectory() as tmp:
            tpl = Path(tmp) / "t.j2"
            tpl.write_text("{{ bad }}", encoding="utf-8")
            try:
                _jinja.render(tpl, Data(name="x"))
            except AlreadyReportedError as wrapper:
                source = wrapper.source
                self.assertIsInstance(source, RuntimeError)
                self.assertIn("bad 求值失败", str(source))
                self.assertIsInstance(source.__cause__, ValueError)
                return
            self.fail("expected AlreadyReportedError")

    def test_model_method_error_during_render(self) -> None:
        class Data:
            def boom(self) -> str:
                raise RuntimeError("method boom")

        with tempfile.TemporaryDirectory() as tmp:
            tpl = Path(tmp) / "t.j2"
            tpl.write_text("{{ boom() }}", encoding="utf-8")
            inst = Data()
            globals_var = {"boom": inst.boom}
            try:
                _jinja.render(tpl, inst, globals_var)
            except AlreadyReportedError as wrapper:
                self.assertIsInstance(wrapper.source, RuntimeError)
                self.assertIn("method boom", str(wrapper.source))
                return
            self.fail("expected AlreadyReportedError")


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
