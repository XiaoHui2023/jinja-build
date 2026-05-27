import sys
import tempfile
import unittest
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from jinja2.exceptions import TemplateSyntaxError, UndefinedError

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from _utils._jinja_env import resolve_template_name  # noqa: E402
from _utils._jinja_errors import build_template_error_report  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
