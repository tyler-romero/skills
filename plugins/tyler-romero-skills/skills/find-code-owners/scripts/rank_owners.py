#!/usr/bin/env python3
"""Rank likely code owners from recency-weighted Git history."""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path


FIELD_SEPARATOR = "\x1f"
BOT_PATTERN = re.compile(
    r"(?:\[bot\]|dependabot|renovate|github-actions|buildkite|automation|bot@)",
    re.IGNORECASE,
)


@dataclass
class Candidate:
    name: str
    email: str
    weighted_score: float = 0.0
    commits: set[str] = field(default_factory=set)
    paths: set[str] = field(default_factory=set)
    path_scores: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    last_timestamp: int = 0
    exact_commits: int = 0
    directory_commits: int = 0


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def repository_root() -> Path:
    return Path(git("rev-parse", "--show-toplevel").strip())


def changed_paths(root: Path) -> list[str]:
    tracked = git("diff", "--name-only", "--diff-filter=ACMR", "HEAD").splitlines()
    untracked = git("ls-files", "--others", "--exclude-standard").splitlines()
    return normalize_paths(root, [*tracked, *untracked])


def normalize_paths(root: Path, paths: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw_path in paths:
        candidate = Path(raw_path)
        if candidate.is_absolute():
            try:
                candidate = candidate.resolve().relative_to(root.resolve())
            except ValueError as error:
                raise ValueError(f"path is outside repository: {raw_path}") from error
        value = candidate.as_posix()
        if value.startswith("./"):
            value = value[2:]
        if not value or value.startswith("../"):
            raise ValueError(f"invalid repository path: {raw_path}")
        if value not in seen:
            seen.add(value)
            normalized.append(value)
    return normalized


def history(path: str, max_commits: int, follow: bool) -> list[tuple[str, str, str, int]]:
    args = [
        "log",
        "--use-mailmap",
        f"--max-count={max_commits}",
        f"--format=%H{FIELD_SEPARATOR}%aN{FIELD_SEPARATOR}%aE{FIELD_SEPARATOR}%at",
    ]
    if follow:
        args.append("--follow")
    args.extend(["--", path])
    records = []
    for line in git(*args).splitlines():
        parts = line.split(FIELD_SEPARATOR)
        if len(parts) != 4:
            continue
        commit, name, email, timestamp = parts
        records.append((commit, name, email, int(timestamp)))
    return records


def github_login(email: str) -> str | None:
    match = re.match(r"(?:\d+\+)?([^@]+)@users\.noreply\.github\.com$", email, re.I)
    return match.group(1) if match else None


def identity_key(name: str, email: str) -> str:
    login = github_login(email)
    if login:
        return f"github:{login.lower()}"
    normalized_name = re.sub(r"\W+", "", name, flags=re.UNICODE).lower()
    return f"name:{normalized_name}" if normalized_name else f"email:{email.lower()}"


def is_excluded(name: str, email: str, exclusions: list[str]) -> bool:
    identity = f"{name} <{email}>"
    if BOT_PATTERN.search(identity):
        return True
    lowered = identity.lower()
    return any(exclusion.lower() in lowered for exclusion in exclusions)


def add_history(
    candidates: dict[str, Candidate],
    path: str,
    records: list[tuple[str, str, str, int]],
    half_life_days: float,
    source_weight: float,
    exclusions: list[str],
    exact: bool,
) -> None:
    now = int(time.time())
    decay = math.log(2) / half_life_days
    for commit, name, email, timestamp in records:
        if is_excluded(name, email, exclusions):
            continue
        age_days = max(0.0, (now - timestamp) / 86400)
        score = source_weight * math.exp(-decay * age_days)
        key = identity_key(name, email)
        candidate = candidates.setdefault(key, Candidate(name=name, email=email))
        if timestamp >= candidate.last_timestamp:
            candidate.name = name
            candidate.email = email
        candidate.weighted_score += score
        candidate.commits.add(commit)
        candidate.paths.add(path)
        candidate.path_scores[path] += score
        candidate.last_timestamp = max(candidate.last_timestamp, timestamp)
        if exact:
            candidate.exact_commits += 1
        else:
            candidate.directory_commits += 1


def rank_paths(
    paths: list[str],
    max_commits: int,
    half_life_days: float,
    exclusions: list[str],
) -> list[Candidate]:
    candidates: dict[str, Candidate] = {}
    for path in paths:
        exact_records = history(path, max_commits, follow=True)
        add_history(
            candidates,
            path,
            exact_records,
            half_life_days,
            source_weight=1.0,
            exclusions=exclusions,
            exact=True,
        )
        if len(exact_records) < 3:
            parent = str(Path(path).parent)
            if parent not in ("", "."):
                directory_records = history(parent, max_commits, follow=False)
                add_history(
                    candidates,
                    path,
                    directory_records,
                    half_life_days,
                    source_weight=0.25,
                    exclusions=exclusions,
                    exact=False,
                )
    return sorted(
        candidates.values(),
        key=lambda candidate: (
            candidate.weighted_score,
            len(candidate.paths),
            candidate.last_timestamp,
        ),
        reverse=True,
    )


def serialize(candidate: Candidate, include_emails: bool) -> dict[str, object]:
    strongest_paths = sorted(
        candidate.path_scores.items(), key=lambda item: item[1], reverse=True
    )
    result: dict[str, object] = {
        "name": candidate.name,
        "github_login": github_login(candidate.email),
        "score": round(candidate.weighted_score, 4),
        "commits": len(candidate.commits),
        "coverage": len(candidate.paths),
        "paths": sorted(candidate.paths),
        "strongest_paths": [
            {"path": path, "score": round(score, 4)}
            for path, score in strongest_paths[:5]
        ],
        "exact_commits": candidate.exact_commits,
        "directory_commits": candidate.directory_commits,
        "last_commit_unix": candidate.last_timestamp,
    }
    if include_emails:
        result["email"] = candidate.email
    return result


def print_table(candidates: list[Candidate], limit: int) -> None:
    print("rank  score   coverage  commits  last activity  candidate")
    for rank, candidate in enumerate(candidates[:limit], start=1):
        last_activity = time.strftime(
            "%Y-%m-%d", time.localtime(candidate.last_timestamp)
        )
        login = github_login(candidate.email)
        identity = f"@{login}" if login else candidate.name
        print(
            f"{rank:>4}  {candidate.weighted_score:>6.2f}  "
            f"{len(candidate.paths):>8}  {len(candidate.commits):>7}  "
            f"{last_activity}  {identity}"
        )
        strongest = sorted(
            candidate.path_scores.items(), key=lambda item: item[1], reverse=True
        )[:3]
        print("      " + ", ".join(path for path, _ in strongest))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Repository-relative paths")
    parser.add_argument("--half-life-days", type=float, default=180.0)
    parser.add_argument("--max-commits", type=int, default=200)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--exclude", action="append", default=[])
    parser.add_argument("--include-emails", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.half_life_days <= 0 or args.max_commits <= 0 or args.limit <= 0:
        print("numeric options must be positive", file=sys.stderr)
        return 2

    try:
        root = repository_root()
        paths = normalize_paths(root, args.paths) if args.paths else changed_paths(root)
        if not paths:
            raise ValueError("no paths supplied and no working-tree changes found")
        candidates = rank_paths(
            paths,
            max_commits=args.max_commits,
            half_life_days=args.half_life_days,
            exclusions=args.exclude,
        )
    except (RuntimeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(
            {
                "repository": str(root),
                "paths": paths,
                "candidates": [
                    serialize(candidate, args.include_emails)
                    for candidate in candidates[: args.limit]
                ],
            },
            indent=2,
        ))
    else:
        print(f"repository: {root}")
        print("paths: " + ", ".join(paths))
        if candidates:
            print_table(candidates, args.limit)
        else:
            print("No non-bot authors found in the selected history.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
