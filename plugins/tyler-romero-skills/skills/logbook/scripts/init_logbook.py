#!/usr/bin/env python3
"""Initialize a logbook without overwriting existing content."""

from __future__ import annotations

import argparse
import os
from pathlib import Path


README = """# Logbook

This directory stores daily work history and cross-session experiment status.

## Files

- `daily/YYYY-MM-DD.md`: append-only daily entries using the local calendar date.
- `experiments.md`: one row per exact experiment name.

## Experiment schema

| Column | Meaning |
| --- | --- |
| Experiment | Exact job or run name; row identity |
| Status | 🟡 running, ⏳ waiting, 🟢 completed, or 🔴 blocked |
| Started | Local date as YYYY-MM-DD, or — |
| Last checked | ISO 8601 timestamp with UTC offset, or — |
| Source | System that supplied the latest status |
| Next check | Follow-up time or condition, or — |
| Notes | Brief context for a future session |

Preserve exact experiment names. Never delete daily entries; append corrections or follow-ups.
"""

EXPERIMENTS = """# Experiments

| Experiment | Status | Started | Last checked | Source | Next check | Notes |
| --- | --- | --- | --- | --- | --- | --- |
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create missing files for a local work and experiment logbook."
    )
    parser.add_argument(
        "--logbook-dir",
        type=Path,
        help="Destination directory. Defaults to LOGBOOK_DIR or ~/.cache/agent-skills/logbook.",
    )
    return parser.parse_args()


def resolve_logbook_dir(argument: Path | None) -> Path:
    if argument is not None:
        return argument.expanduser()
    if configured := os.environ.get("LOGBOOK_DIR"):
        return Path(configured).expanduser()
    return Path.home() / ".cache" / "agent-skills" / "logbook"


def create_file(path: Path, content: str) -> bool:
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(content)
    except FileExistsError:
        if not path.is_file():
            raise SystemExit(f"Expected a file but found another path type: {path}")
        return False
    return True


def main() -> int:
    root = resolve_logbook_dir(parse_args().logbook_dir)
    if root.exists() and not root.is_dir():
        raise SystemExit(f"Logbook path exists but is not a directory: {root}")

    daily = root / "daily"
    daily.mkdir(parents=True, exist_ok=True)

    results = {
        root / "README.md": create_file(root / "README.md", README),
        root / "experiments.md": create_file(root / "experiments.md", EXPERIMENTS),
    }

    print(f"Logbook ready: {root}")
    print("daily/: ready")
    for path, created in results.items():
        state = "created" if created else "preserved existing"
        print(f"{path.name}: {state}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
