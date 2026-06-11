import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from jinja2.exceptions import TemplateSyntaxError, UndefinedError

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from _utils._jinja_env import resolve_template_name  # noqa: E402
from _utils._jinja_errors import (  # noqa: E402
    _entry_path_in_sites,
    _is_internal_python_frame,
    build_render_user_error_report,
    build_template_error_report,
)


class InternalFrameTests(unittest.TestCase):
    def test_utils_and_core_paths_are_internal(self) -> None:
        self.assertTrue(_is_internal_python_frame(r"F:\proj\src\_utils\_jinja_view.py"))
        self.assertTrue(_is_internal_python_frame("/app/src/_utils/__init__.py"))
        self.assertTrue(_is_internal_python_frame(r"F:\proj\src\_core.py"))
        self.assertTrue(_is_internal_python_frame(r"F:\proj\src\__main__.py"))

    def test_models_and_helper_paths_are_user(self) -> None:
        self.assertFalse(_is_internal_python_frame(r"F:\templates\models.py"))
        self.assertFalse(_is_internal_python_frame(r"F:\templates\helper.py"))

    def test_meipass_bundle_paths_are_internal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            meipass = Path(tmp) / "_MEI12345"
            utils_file = meipass / "_utils" / "_jinja.py"
            utils_file.parent.mkdir(parents=True)
            utils_file.write_text("x = 1\n", encoding="utf-8")
            with mock.patch.object(sys, "_MEIPASS", str(meipass), create=True):
                self.assertTrue(_is_internal_python_frame(str(utils_file)))


class ResolveTemplateNameTests(unittest.TestCase):
    def test_relative_to_search_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested = root / "partials"
            nested.mkdir()
            tpl = nested / "item.j2"
            tpl.write_text("x", encoding="utf-8")
            name = resolve_template_name(tpl, [root])
            self.assertEqual(name, "partials/item.j2")

    def test_falls_back_to_basename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tpl = Path(tmp) / "only.j2"
            tpl.write_text("x", encoding="utf-8")
            self.assertEqual(resolve_template_name(tpl, []), "only.j2")


class TemplateErrorReportTests(unittest.TestCase):
    def test_syntax_error_includes_line_and_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.j2"
            path.write_text("ok\n{% if %}\n", encoding="utf-8")
            env = Environment(undefined=StrictUndefined, loader=FileSystemLoader([tmp]))
            try:
                env.get_template("bad.j2")
            except TemplateSyntaxError as exc:
                report = build_template_error_report(exc, entry_path=path)
                self.assertEqual(report.exc_type, "TemplateSyntaxError")
                self.assertIn("expression", report.message.lower())
                self.assertEqual(len(report.sites), 1)
                self.assertEqual(report.sites[0].lineno, 2)
                self.assertIn("if", report.sites[0].line_text)
                return
            self.fail("expected TemplateSyntaxError")

    def test_undefined_error_maps_to_template_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.j2"
            path.write_text("a\n{{ missing }}\n", encoding="utf-8")
            env = Environment(undefined=StrictUndefined, loader=FileSystemLoader([tmp]))
            try:
                env.get_template("t.j2").render({})
            except UndefinedError as exc:
                report = build_template_error_report(exc, entry_path=path)
                self.assertEqual(report.exc_type, "UndefinedError")
                self.assertIn("missing", report.message)
                self.assertEqual(report.sites[0].lineno, 2)
                self.assertIn("missing", report.sites[0].line_text)
                return
            self.fail("expected UndefinedError")

    def test_entry_meta_skipped_when_site_covers_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.j2"
            path.write_text("{{ missing }}\n", encoding="utf-8")
            env = Environment(undefined=StrictUndefined, loader=FileSystemLoader([tmp]))
            try:
                env.get_template("t.j2").render({})
            except UndefinedError as exc:
                report = build_template_error_report(exc, entry_path=path)
                self.assertTrue(_entry_path_in_sites(report))
                return
            self.fail("expected UndefinedError")


class RenderUserErrorReportDedupTests(unittest.TestCase):
    def test_context_property_error_omits_template_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            models_path = Path(tmp) / "models.py"
            models_path.write_text(
                "class Data:\n"
                "    @property\n"
                "    def bad(self):\n"
                "        raise ValueError('prop boom')\n",
                encoding="utf-8",
            )
            tpl = Path(tmp) / "t.j2"
            tpl.write_text("{{ bad }}\n", encoding="utf-8")
            namespace: dict[str, object] = {}
            code = compile(models_path.read_text(encoding="utf-8"), str(models_path), "exec")
            exec(code, namespace)
            inst = namespace["Data"]()
            from _utils._jinja_convert import read_property_value  # noqa: E402

            try:
                read_property_value(inst, "bad")
            except RuntimeError as exc:
                report = build_render_user_error_report(exc, entry_path=tpl)
                template_sites = [site for site in report.sites if site.path.resolve() == tpl.resolve()]
                model_sites = [
                    site for site in report.sites if site.path.resolve() == models_path.resolve()
                ]
                self.assertEqual(len(template_sites), 0)
                self.assertEqual(len(model_sites), 1)
                for site in report.sites:
                    self.assertNotIn("/_utils/", site.path.as_posix())
                return
            self.fail("expected RuntimeError")


if __name__ == "__main__":
    unittest.main()
