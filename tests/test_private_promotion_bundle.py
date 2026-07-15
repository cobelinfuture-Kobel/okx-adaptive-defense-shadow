from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "ci"
    / "build_private_promotion_bundle.py"
)
SPEC = importlib.util.spec_from_file_location("promotion_bundle", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
bundle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bundle)


class PrivatePromotionBundleTests(unittest.TestCase):
    def test_rejects_sensitive_paths(self) -> None:
        for path in (
            ".env",
            ".env.production",
            "Setting.txt",
            "Strategy.txt",
            "logs/runtime.log",
            "data/live.json",
            "artifacts/evidence.json",
            "private.pem",
            "runtime.csv",
        ):
            with self.subTest(path=path):
                with self.assertRaises(RuntimeError):
                    bundle.validate_path(path)

    def test_allows_sanitized_paths(self) -> None:
        for path in (
            "README.md",
            ".env.example",
            "docs/contract.md",
            "governance/public_task_queue.json",
            "tests/fixtures/synthetic.json",
        ):
            with self.subTest(path=path):
                bundle.validate_path(path)

    def test_digest_changes_with_content(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            target = root / "a.txt"
            target.write_text("a", encoding="utf-8")
            first = bundle.tree_digest(root, ["a.txt"])
            target.write_text("b", encoding="utf-8")
            second = bundle.tree_digest(root, ["a.txt"])
            self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
