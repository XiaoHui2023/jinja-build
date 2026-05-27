from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from _utils._config_bundle import (  # noqa: E402
    is_config_bundle_text,
    load_bundle_config,
    parse_config_bundle,
)


class TestConfigBundle(unittest.TestCase):
    def test_parse_sections(self) -> None:
        text = textwrap.dedent(
            """
            #a.yaml
            key: 1

            #b.json
            {"x": 2}
            """
        ).strip()
        self.assertTrue(is_config_bundle_text(text))
        sections = parse_config_bundle(text)
        self.assertEqual([name for name, _ in sections], ["a.yaml", "b.json"])
        self.assertIn("key: 1", sections[0][1])

    def test_load_user_multifile_example(self) -> None:
        bundle = textwrap.dedent(
            """
            #a.yaml
            !include spec.yaml
            class_prefix: CLock_
            trees:
              - name: orion
              - nodes: ${vars.nodes}

            # spec.yaml
            vars:
              nodes:
                !include b.json
                !include c.yaml

            # b.json
            {
              "a": {"name": 6},
              "b": {"name": 7}
            }

            # c.yaml
            a:
              freq: 128
            """
        ).strip() + "\n"

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bundle.yaml"
            path.write_text(bundle, encoding="utf-8")
            loaded = load_bundle_config(path)
            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(loaded["class_prefix"], "CLock_")
            self.assertEqual(loaded["vars"]["nodes"]["a"]["freq"], 128)
            self.assertEqual(loaded["trees"][1]["nodes"]["b"]["name"], 7)

    def test_non_bundle_returns_none(self) -> None:
        text = "class_prefix: X\n"
        self.assertFalse(is_config_bundle_text(text))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plain.yaml"
            path.write_text(text, encoding="utf-8")
            self.assertIsNone(load_bundle_config(path))


if __name__ == "__main__":
    unittest.main()
