#!/usr/bin/env python3
"""Validate that cross-platform plugin adapters point at the same skills."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "tyler-romero-skills"
EXPECTED_NAME = "tyler-romero-skills"
EXPECTED_VERSION = "0.1.0"
EXPECTED_SOURCE = "./plugins/tyler-romero-skills"


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"{path.relative_to(ROOT)}: {error}") from error


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_skill(path: Path) -> str:
    text = path.read_text()
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    require(match is not None, f"{path.relative_to(ROOT)}: missing YAML frontmatter")
    frontmatter = match.group(1)
    name = re.search(r"^name:\s*(.+)$", frontmatter, re.MULTILINE)
    description = re.search(r"^description:\s*\S.*$", frontmatter, re.MULTILINE)
    require(name is not None, f"{path.relative_to(ROOT)}: missing name")
    require(description is not None, f"{path.relative_to(ROOT)}: missing description")
    skill_name = name.group(1).strip().strip('"\'')
    require(path.parent.name == skill_name, f"{path.relative_to(ROOT)}: folder/name mismatch")
    return skill_name


def main() -> int:
    try:
        copilot = load_json(PLUGIN / "plugin.json")
        claude = load_json(PLUGIN / ".claude-plugin" / "plugin.json")
        codex = load_json(PLUGIN / ".codex-plugin" / "plugin.json")
        shared_marketplace = load_json(ROOT / ".claude-plugin" / "marketplace.json")
        codex_marketplace = load_json(ROOT / ".agents" / "plugins" / "marketplace.json")

        for label, manifest in (("Copilot", copilot), ("Claude", claude), ("Codex", codex)):
            require(manifest.get("name") == EXPECTED_NAME, f"{label}: plugin name mismatch")
            require(manifest.get("version") == EXPECTED_VERSION, f"{label}: version mismatch")

        require(copilot.get("skills") == ["skills/"], "Copilot: skills path mismatch")
        require(claude.get("skills") == "./skills/", "Claude: skills path mismatch")
        require(codex.get("skills") == "./skills/", "Codex: skills path mismatch")

        require(shared_marketplace.get("name") == EXPECTED_NAME, "Claude/Copilot marketplace name mismatch")
        require(codex_marketplace.get("name") == EXPECTED_NAME, "Codex marketplace name mismatch")

        shared_entry = shared_marketplace["plugins"][0]
        codex_entry = codex_marketplace["plugins"][0]
        require(shared_entry.get("name") == EXPECTED_NAME, "Claude/Copilot marketplace plugin mismatch")
        require(codex_entry.get("name") == EXPECTED_NAME, "Codex marketplace plugin mismatch")
        require(shared_entry.get("version") == EXPECTED_VERSION, "Claude/Copilot marketplace version mismatch")
        require(shared_entry.get("source") == EXPECTED_SOURCE, "Shared marketplace source mismatch")
        require(codex_entry["source"].get("path") == EXPECTED_SOURCE, "Codex marketplace source mismatch")

        skill_files = sorted((PLUGIN / "skills").glob("*/SKILL.md"))
        require(bool(skill_files), "No skills found")
        skill_names = [validate_skill(path) for path in skill_files]
    except (KeyError, IndexError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: {EXPECTED_NAME} {EXPECTED_VERSION}")
    print(f"OK: {len(skill_names)} shared skill(s): {', '.join(skill_names)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
