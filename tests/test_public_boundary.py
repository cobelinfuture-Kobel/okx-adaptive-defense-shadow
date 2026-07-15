from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "ci"
    / "validate_public_boundary.py"
)
SPEC = importlib.util.spec_from_file_location("validate_public_boundary", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class PublicBoundaryTests(unittest.TestCase):
    def test_blocks_operational_files(self) -> None:
        for path in (
            ".env",
            ".env.production",
            "Setting.txt",
            "Strategy.txt",
            "logs/runtime.log",
            "data/runtime_config.json",
            "artifacts/report.json",
            "private.pem",
            "runtime.csv",
        ):
            with self.subTest(path=path):
                self.assertTrue(validator.validate_path(path))

    def test_allows_public_contract_files(self) -> None:
        for path in (
            "README.md",
            ".env.example",
            "docs/PUBLIC_PRIVATE_PROMOTION_CONTRACT.md",
            "governance/public_task_queue.json",
            "tests/fixtures/synthetic_market.json",
        ):
            with self.subTest(path=path):
                self.assertEqual([], validator.validate_path(path))

    def test_queue_safety_contract(self) -> None:
        self.assertEqual([], validator.validate_queue())


if __name__ == "__main__":
    unittest.main()
