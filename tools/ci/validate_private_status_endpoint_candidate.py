from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


SNAPSHOT_P95_MS = 250.0
ROUTE_P95_MS = 500.0
SLOW_INJECTION_MAX_MS = 500.0
EXPECTED_EVIDENCE = (
    "docs/roadmap/runtime_recovery/fullfix_retry/s0/latency_measurements.json",
    "docs/roadmap/runtime_recovery/readback_qa_retry/s0/latest.json",
)
FORBIDDEN_NAMES = {".env", "setting.txt", "strategy.txt"}


def _run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False)


def _fail(summary: dict[str, Any], classification: str) -> int:
    summary["verdict"] = classification
    print(json.dumps(summary, sort_keys=True))
    return 1


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _candidate_files(root: Path) -> list[str]:
    result = _run(["git", "ls-files", "-z"], cwd=root)
    if result.returncode:
        return []
    return [entry.decode("utf-8") for entry in result.stdout.encode("utf-8").split(b"\0") if entry]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-root", required=True)
    parser.add_argument("--candidate-sha", required=True)
    args = parser.parse_args()
    root = Path(args.candidate_root).resolve()
    summary: dict[str, Any] = {
        "task_id": "RuntimeRecovery-S0_StatusEndpointLatency_PublicCI_Retry",
        "candidate_sha": args.candidate_sha,
        "shadow_only": True,
        "effective": False,
        "execution_allowed": False,
        "okx_api_accessed": False,
        "orders_modified": False,
    }
    head = _run(["git", "rev-parse", "HEAD"], cwd=root)
    if head.returncode or head.stdout.strip() != args.candidate_sha:
        return _fail(summary, "CANDIDATE_SHA_MISMATCH")
    summary["checked_out_sha"] = head.stdout.strip()

    tracked = _candidate_files(root)
    if not tracked or any(Path(item).name.lower() in FORBIDDEN_NAMES for item in tracked):
        return _fail(summary, "SENSITIVE_BOUNDARY_FAILURE")
    summary["sensitive_output_scan"] = "PASS"

    try:
        latency_evidence = _read_json(root / EXPECTED_EVIDENCE[0])
        readback_evidence = _read_json(root / EXPECTED_EVIDENCE[1])
    except (OSError, json.JSONDecodeError):
        return _fail(summary, "EVIDENCE_JSON_FAILURE")
    if latency_evidence.get("fixture_sha256") != "91890b43a443649a8c8eb34df6979bc18eeba7a41315314b993ecd15a099cf61" or readback_evidence.get("status") != "PASS":
        return _fail(summary, "EVIDENCE_CONTRACT_FAILURE")
    summary["fixture_sha256"] = latency_evidence["fixture_sha256"]
    summary["evidence_json_parse"] = "PASS"

    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    tests = _run(
        [sys.executable, "-m", "pytest", "-q", "tests/test_status_snapshot.py", "tests/test_adaptive_defense.py::test_status_api_exposes_risk_archetype_suppression_metadata_like_runtime_status"],
        cwd=root,
        env=env,
    )
    passed = re.search(r"(\d+) passed", tests.stdout)
    if tests.returncode or not passed:
        return _fail(summary, "FOCUSED_TEST_FAILURE")
    summary["focused_tests"] = {"passed": int(passed.group(1)), "failed": 0}

    harness = _run([sys.executable, "tests/runtime_status_latency_harness.py"], cwd=root, env=env)
    try:
        measurements = json.loads(harness.stdout)
        dependencies = measurements["injected_slow_dependencies"]["dependencies"]
        valid_latency = (
            measurements["snapshot_reader"]["p95_ms"] < SNAPSHOT_P95_MS
            and measurements["in_process_route"]["p95_ms"] < ROUTE_P95_MS
            and measurements["injected_slow_dependencies"]["max_ms"] < SLOW_INJECTION_MAX_MS
            and all(item["call_count"] == 0 for item in dependencies)
            and measurements["fixture_sha256"] == summary["fixture_sha256"]
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return _fail(summary, "LATENCY_HARNESS_FAILURE")
    if harness.returncode or not valid_latency:
        return _fail(summary, "LATENCY_GATE_FAILURE")
    summary["latency"] = {
        "snapshot_p95_ms": measurements["snapshot_reader"]["p95_ms"],
        "snapshot_threshold_ms": SNAPSHOT_P95_MS,
        "route_p95_ms": measurements["in_process_route"]["p95_ms"],
        "route_threshold_ms": ROUTE_P95_MS,
        "slow_injection_max_ms": measurements["injected_slow_dependencies"]["max_ms"],
        "slow_injection_threshold_ms": SLOW_INJECTION_MAX_MS,
    }
    summary["legacy_builder_call_counts"] = [item["call_count"] for item in dependencies]

    compile_result = _run([sys.executable, "-m", "compileall", "-q", "api/status_snapshot.py", "api/routes_status.py", "tests/test_status_snapshot.py", "tests/runtime_status_latency_harness.py"], cwd=root, env=env)
    diff_result = _run(["git", "diff", "--check"], cwd=root)
    if compile_result.returncode or diff_result.returncode:
        return _fail(summary, "STATIC_VALIDATION_FAILURE")
    summary["compile_static_validation"] = "PASS"
    summary["git_diff_check"] = "PASS"
    summary["verdict"] = "PUBLIC_CI_PASS"
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
