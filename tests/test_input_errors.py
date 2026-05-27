import sys
import tempfile
import textwrap
import unittest
from io import StringIO
from pathlib import Path
from unittest import mock

from pydantic import BaseModel, ValidationError

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from _utils._input_errors import (  # noqa: E402
    build_input_load_error_report,
    print_input_model_error,
)
from _utils._jinja_rich import jinja_error_console  # noqa: E402


class Item(BaseModel):
    name: str
    qty: int


class Data(BaseModel):
    items: list[Item]


class InputErrorReportTests(unittest.TestCase):
    def test_validation_error_collects_all_fields(self) -> None:
        try:
            Data(items=[{"name": "a"}, {"name": "b", "qty": "x"}])
        except ValidationError as exc:
            report = build_input_load_error_report(
                exc,
                input_path=Path("in.json"),
                models_path=Path("template/models.py"),
                models_type=Data,
                stage="model",
            )

        self.assertEqual(report.exc_type, "ValidationError")
        self.assertEqual(len(report.field_errors), 2)
        self.assertEqual(report.field_errors[0].loc, "items[0].qty")
        self.assertEqual(report.field_errors[1].loc, "items[1].qty")
        self.assertIn("qty", report.field_errors[0].loc)
        self.assertEqual(report.models_type_name, "Data")

    def test_type_error_includes_init_hints(self) -> None:
        class Plain:
            def __init__(self, name: str) -> None:
                self.name = name

        try:
            Plain(unknown=1)  # type: ignore[call-arg]
        except TypeError as exc:
            report = build_input_load_error_report(
                exc,
                input_path=None,
                models_path=Path("models.py"),
                models_type=Plain,
                stage="model",
            )

        self.assertTrue(any("__init__ 参数" in hint for hint in report.hints))

    def test_print_writes_rich_output(self) -> None:
        try:
            Data(items=[{"name": "only"}])
        except ValidationError as exc:
            buffer = StringIO()
            shared = jinja_error_console()
            shared.file = buffer
            with mock.patch(
                "_utils._input_errors.jinja_error_console",
                return_value=shared,
            ):
                print_input_model_error(
                    exc,
                    input_path=Path("cfg.json"),
                    models_path=Path("template/models.py"),
                    models_type=Data,
                    stage="model",
                )
            text = buffer.getvalue()
            self.assertIn("ValidationError", text)
            self.assertIn("items[0].qty", text)
            self.assertIn("cfg.json", text)


class CoreInputErrorIntegrationTests(unittest.TestCase):
    def test_pydantic_validation_still_raises(self) -> None:
        from _case import TemplateProject  # noqa: E402

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
                    """
                )
            )
            p.write_json("in.json", {"items": [{"name": "a"}]})
            p.write_template("x.txt.j2", "{{ items[0].name }}\n")
            with self.assertRaises(ValidationError):
                p.run(input_path=str(p.root / "in.json"))


if __name__ == "__main__":
    unittest.main()
