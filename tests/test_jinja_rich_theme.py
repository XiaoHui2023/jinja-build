import sys
import unittest
from io import StringIO
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from _utils._jinja_rich import (  # noqa: E402
    configure_jinja_error_theme,
    detect_background,
    jinja_error_console,
    normalize_theme_mode,
    reset_jinja_error_console,
    resolve_background,
    theme_for_background,
)


class ThemeModeTests(unittest.TestCase):
    def tearDown(self) -> None:
        reset_jinja_error_console()

    def test_normalize_invalid_falls_back_to_auto(self) -> None:
        self.assertEqual(normalize_theme_mode("AUTO"), "auto")
        self.assertEqual(normalize_theme_mode("bogus"), "auto")

    def test_resolve_auto_unknown_defaults_dark(self) -> None:
        with mock.patch("_utils._jinja_rich.detect_background", return_value="unknown"):
            self.assertEqual(resolve_background("auto"), "dark")

    def test_resolve_auto_light(self) -> None:
        with mock.patch("_utils._jinja_rich.detect_background", return_value="light"):
            self.assertEqual(resolve_background("auto"), "light")

    def test_colorfgbg_dark(self) -> None:
        with mock.patch.dict("os.environ", {"COLORFGBG": "15;0"}, clear=False):
            self.assertEqual(detect_background(), "dark")

    def test_colorfgbg_light(self) -> None:
        with mock.patch.dict("os.environ", {"COLORFGBG": "0;15"}, clear=False):
            self.assertEqual(detect_background(), "light")

    def test_configure_none_disables_color(self) -> None:
        configure_jinja_error_theme("none")
        console = jinja_error_console()
        self.assertTrue(console.no_color)

    def test_configure_dark_uses_dark_theme(self) -> None:
        configure_jinja_error_theme("dark")
        console = jinja_error_console()
        self.assertEqual(
            console.get_style("error.message").color,
            theme_for_background("dark").styles["error.message"].color,
        )

    def test_configure_light_uses_light_theme(self) -> None:
        configure_jinja_error_theme("light")
        console = jinja_error_console()
        self.assertEqual(
            console.get_style("error.message").color,
            theme_for_background("light").styles["error.message"].color,
        )

    def test_luminance_from_osc_rgb(self) -> None:
        from _utils._jinja_rich import _luminance_from_osc_response  # noqa: E402

        dark = _luminance_from_osc_response("\x1b]11;rgb:1e1e/1e1e/1e1e\x07")
        light = _luminance_from_osc_response("\x1b]11;rgb:ffff/ffff/ffff\x07")
        self.assertIsNotNone(dark)
        self.assertIsNotNone(light)
        assert dark is not None and light is not None
        self.assertLess(dark, 0.5)
        self.assertGreater(light, 0.5)


class MainThemeArgTests(unittest.TestCase):
    def tearDown(self) -> None:
        reset_jinja_error_console()

    def _get_args(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "jinja_build_main",
            SRC / "__main__.py",
        )
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.get_args

    def test_get_args_theme_default_from_env(self) -> None:
        get_args = self._get_args()
        with mock.patch.dict("os.environ", {"JINJA_BUILD_THEME": "dark"}, clear=False):
            with mock.patch("sys.argv", ["jinja-build", "-t", "x", "-o", "y"]):
                args = get_args()
        self.assertEqual(args.theme, "dark")

    def test_get_args_theme_explicit_overrides_env(self) -> None:
        get_args = self._get_args()
        with mock.patch.dict("os.environ", {"JINJA_BUILD_THEME": "dark"}, clear=False):
            with mock.patch(
                "sys.argv",
                ["jinja-build", "-t", "x", "-o", "y", "--theme", "light"],
            ):
                args = get_args()
        self.assertEqual(args.theme, "light")


if __name__ == "__main__":
    unittest.main()
