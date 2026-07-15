from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

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


def run(command: list[str], *, cwd: Path) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def validate_path(path: str) -> None:
    normalized = PurePosixPath(path).as_posix()
    lowered = normalized.lower()
    name = PurePosixPath(lowered).name
    if name in FORBIDDEN_NAMES:
        raise RuntimeError(f"forbidden promotion path: {normalized}")
    if name.startswith(".env.") and name != ".env.example":
        raise RuntimeError(f"forbidden promotion path: {normalized}")
    if lowered.startswith(FORBIDDEN_PREFIXES):
        raise RuntimeError(f"forbidden promotion prefix: {normalized}")
    if lowered.endswith(FORBIDDEN_SUFFIXES):
        raise RuntimeError(f"forbidden promotion suffix: {normalized}")


def tracked_files(public_root: Path) -> list[str]:
    raw = run(["git", "ls-files", "-z"], cwd=public_root)
    files = sorted(value for value in raw.split("\0") if value)
    for path in files:
        validate_path(path)
    return files


def tree_digest(public_root: Path, files: list[str]) -> str:
    digest = hashlib.sha256()
    for path in files:
        target = public_root / path
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(target.read_bytes()).digest())
        digest.update(b"\0")
    return digest.hexdigest()


def copy_tree(
    public_root: Path,
    destination: Path,
    files: list[str],
) -> None:
    temporary = destination.with_name(destination.name + ".tmp")
    if temporary.exists():
        shutil.rmtree(temporary)
    temporary.mkdir(parents=True)
    for path in files:
        source = public_root / path
        target = temporary / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    if destination.exists():
        shutil.rmtree(destination)
    temporary.replace(destination)


def build_bundle(
    *,
    public_root: Path,
    private_root: Path,
    source_sha: str,
    workflow_run_id: str,
    workflow_run_url: str,
) -> dict[str, object]:
    files = tracked_files(public_root)
    digest = tree_digest(public_root, files)
    destination = (
        private_root
        / "public_verified"
        / "okx-adaptive-defense-shadow"
    )
    copy_tree(public_root, destination, files)
    manifest: dict[str, object] = {
        "schema_version": "okx_public_push_private_promotion_v1",
        "status": "PROMOTED_VERIFIED_PUBLIC_SNAPSHOT",
        "public_repository": "cobelinfuture-Kobel/okx-adaptive-defense-shadow",
        "private_repository": "cobelinfuture-Kobel/okx_bot_private",
        "public_main_commit": source_sha,
        "workflow_run_id": workflow_run_id,
        "workflow_run_url": workflow_run_url,
        "tracked_file_count": len(files),
        "tree_digest_sha256": digest,
        "promoted_at": datetime.now(timezone.utc).isoformat(),
        "promotion_direction": "PUBLIC_PUSH_TO_PRIVATE_PUBLIC_VERIFIED_BRANCH",
        "shadow_only": True,
        "effective": False,
        "execution_allowed": False,
        "runtime_proof": "NOT_CLAIMED",
    }
    payload = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    (destination / "_promotion_manifest.json").write_text(
        payload,
        encoding="utf-8",
    )
    latest = (
        private_root
        / "docs"
        / "roadmap"
        / "public_ci"
        / "verified"
        / "latest.json"
    )
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(payload, encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--public-root", required=True, type=Path)
    parser.add_argument("--private-root", required=True, type=Path)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--workflow-run-id", required=True)
    parser.add_argument("--workflow-run-url", required=True)
    args = parser.parse_args()
    try:
        manifest = build_bundle(
            public_root=args.public_root.resolve(),
            private_root=args.private_root.resolve(),
            source_sha=args.source_sha,
            workflow_run_id=args.workflow_run_id,
            workflow_run_url=args.workflow_run_url,
        )
    except Exception as exc:
        print(f"PUBLIC_PROMOTION_FAIL: {exc}")
        return 1
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
