from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "governance" / "public_task_queue.json"

FORBIDDEN_NAMES = {
    ".env",
    "setting.txt",
    "strategy.txt",
    "setting.local.txt",
    "strategy.local.txt",
    "runtime_response.json",
}
FORBIDDEN_PREFIXES = ("logs/", "data/", "artifacts/")
FORBIDDEN_SUFFIXES = (
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".csv",
)
SECRET_PATTERNS = (
    re.compile(r"(?im)^\s*(?:OKX_)?API[_-]?KEY\s*[:=]\s*[^\s<>{}]+"),
    re.compile(r"(?im)^\s*(?:OKX_)?SECRET(?:_KEY)?\s*[:=]\s*[^\s<>{}]+"),
    re.compile(r"(?im)^\s*(?:OKX_)?PASSPHRASE\s*[:=]\s*[^\s<>{}]+"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)
REQUIRED_FORBIDDEN_ACTIONS = {
    "DecisionResolver Effective Path",
    "Sizing Effective Path",
    "Spacing Effective Path",
    "Order Count Effective Path",
    "Auto Reduce",
    "Strategy Rotation",
    "Active Pool Selection",
    "Order Placement",
    "Order Cancellation",
    "Order Movement",
}


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [
        value.decode("utf-8")
        for value in result.stdout.split(b"\0")
        if value
    ]


def validate_path(path: str) -> list[str]:
    normalized = PurePosixPath(path).as_posix()
    lowered = normalized.lower()
    name = PurePosixPath(lowered).name
    errors: list[str] = []
    if name in FORBIDDEN_NAMES or (
        name.startswith(".env.") and name != ".env.example"
    ):
        errors.append(f"forbidden tracked file: {normalized}")
    if lowered.startswith(FORBIDDEN_PREFIXES):
        errors.append(f"forbidden tracked prefix: {normalized}")
    if lowered.endswith(FORBIDDEN_SUFFIXES):
        errors.append(f"forbidden tracked suffix: {normalized}")
    return errors


def validate_content(path: str) -> list[str]:
    target = ROOT / path
    if not target.is_file():
        return []
    try:
        text = target.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    return [
        f"possible secret assignment in: {path}"
        for pattern in SECRET_PATTERNS
        if pattern.search(text)
    ]


def validate_queue() -> list[str]:
    errors: list[str] = []
    payload = json.loads(QUEUE.read_text(encoding="utf-8"))
    safety = payload.get("safety", {})
    expected = {
        "shadow_only": True,
        "effective": False,
        "execution_allowed": False,
        "runtime_access_allowed": False,
        "okx_api_access_allowed": False,
    }
    for key, value in expected.items():
        if safety.get(key) is not value:
            errors.append(f"invalid safety invariant: {key}")
    actual = set(payload.get("forbidden_actions", []))
    missing = sorted(REQUIRED_FORBIDDEN_ACTIONS - actual)
    if missing:
        errors.append("missing forbidden actions: " + ", ".join(missing))

    automation = payload.get("automation", {})
    required = {
        "public_to_private_push_allowed": True,
        "public_to_private_push_scope": "okx_bot_private/public-verified",
        "public_to_private_push_event": "main_after_static_ci_pass",
        "public_to_private_push_on_pull_request": False,
        "private_main_direct_write_allowed": False,
        "private_promotion_secret": "PRIVATE_PROMOTION_TOKEN",
        "runtime_proof_claim_allowed": False,
    }
    for key, value in required.items():
        if automation.get(key) != value:
            errors.append(f"invalid bounded promotion contract: {key}")
    return errors


def main() -> int:
    errors: list[str] = []
    files = tracked_files()
    for path in files:
        errors.extend(validate_path(path))
        errors.extend(validate_content(path))
    errors.extend(validate_queue())
    if errors:
        for error in sorted(set(errors)):
            print(f"FAIL: {error}")
        return 1
    print(f"PASS: public boundary validated for {len(files)} tracked files")
    print("PASS: shadow_only=true effective=false execution_allowed=false")
    print("PASS: bounded promotion targets Private public-verified only")
    return 0


if __name__ == "__main__":
    sys.exit(main())
