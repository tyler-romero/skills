# Tyler Romero Skills

A portable Agent Skills repository for GitHub Copilot, Claude Code, and OpenAI Codex.

The skill content is defined once under `plugins/tyler-romero-skills/skills/`. Each host gets only the small manifest or marketplace file it needs.

## How portability works

All three hosts support the open Agent Skills shape: a directory containing a `SKILL.md` file with `name` and `description` YAML frontmatter. Their plugin packaging is not yet standardized, so this repository supplies parallel adapters around one shared skill tree.

```text
.
├── .agents/plugins/marketplace.json           # Codex marketplace
├── .claude-plugin/marketplace.json             # Claude + Copilot marketplace
└── plugins/tyler-romero-skills/
    ├── plugin.json                             # GitHub Copilot manifest
    ├── .claude-plugin/plugin.json              # Claude Code manifest
    ├── .codex-plugin/plugin.json               # Codex manifest
    └── skills/
        ├── chrome-cdp/                          # Control authenticated Chrome tabs
        ├── grill-me/                            # Stress-test plans and designs
        ├── handoff/                             # Prepare work for a fresh agent
        ├── local-code-review/                   # Review without modifying a PR
        ├── portable-smoke-test/                 # Verify cross-host loading
        └── read-arxiv-paper/                    # Analyze papers from TeX source
```

The extra manifest and metadata files are additive. Hosts ignore files they do not understand.

`read-arxiv-paper` is adapted from `karpathy/nanochat` and retains its upstream MIT license in the skill directory.

## Current compatibility

| Host | Plugin install | Shared `SKILL.md` | Important limitation |
| --- | --- | --- | --- |
| GitHub Copilot CLI | Yes | Yes | Copilot plugins are currently CLI-only. Other Copilot surfaces discover repository/user skills instead. |
| Claude Code | Yes | Yes | Plugin skills are namespaced by plugin when invoked explicitly. |
| OpenAI Codex | Yes | Yes | Codex uses its own plugin manifest and marketplace catalog. |

For GitHub Copilot coding agent or editor discovery without the CLI plugin, copy or symlink a skill folder into a supported skill location such as `.github/skills`, `.agents/skills`, or `$HOME/.copilot/skills`, depending on the surface and desired scope.

## Install

These examples use the repository's current GitHub slug, `tyler-romero/skills`.

### GitHub Copilot CLI

```text
/plugin marketplace add tyler-romero/skills
/plugin install tyler-romero-skills@tyler-romero-skills
```

The equivalent terminal commands are:

```bash
copilot plugin marketplace add tyler-romero/skills
copilot plugin install tyler-romero-skills@tyler-romero-skills
```

### Claude Code

```text
/plugin marketplace add tyler-romero/skills
/plugin install tyler-romero-skills@tyler-romero-skills
```

### OpenAI Codex

```bash
codex plugin marketplace add tyler-romero/skills
codex plugin add tyler-romero-skills@tyler-romero-skills
```

Start a new task/session after installation so the host reloads its available skills.

## Sync installations

Run the cross-platform updater:

```bash
./scripts/sync-all.sh
```

It updates `tyler-romero-skills` wherever it is already installed. When a supported CLI is present but the plugin is missing, the script adds the `tyler-romero/skills` marketplace and installs it. Missing CLIs are reported and skipped. A real installation or update failure returns a nonzero exit code. The script requires Bash and Python 3.

The sync also installs or upgrades the maintained [`github/gh-stack`](https://github.com/github/gh-stack) GitHub CLI extension and installs its upstream `gh-stack` Agent Skill for Copilot, Claude Code, and Codex. The upstream skill remains source-tracked, so it can be refreshed without vendoring it into this repository.

To install the dependency manually instead:

```bash
gh extension install github/gh-stack

for agent in github-copilot claude-code codex; do
  gh skill install github/gh-stack gh-stack --agent "$agent" --scope user --force
done
```

The `gh skill` command is currently a GitHub CLI preview feature.

## Run the smoke test

Ask naturally in any host:

```text
Run the portable skill smoke test for violet-otter.
```

Expected response:

```text
PORTABLE_SKILL_OK
skill: portable-smoke-test
token: violet-otter
```

Explicit invocation is host-specific:

- Claude Code: `/tyler-romero-skills:portable-smoke-test Run for violet-otter.`
- Codex: `Use $portable-smoke-test to run for violet-otter.`
- Copilot CLI: select the skill with `/skills` or ask with the natural trigger above.

## Add another skill

Create one folder under `plugins/tyler-romero-skills/skills/`:

```text
skills/my-skill/
└── SKILL.md
```

Use portable frontmatter:

```markdown
---
name: my-skill
description: Explain what the skill does and the phrases or tasks that should trigger it.
---

# My Skill

Write imperative instructions here.
```

Keep platform-specific metadata optional and adjacent to the shared definition. Avoid relying on host-only frontmatter fields, invocation syntax, or tools in the portable core unless the skill deliberately targets one host.

Run the repository validator after changes:

```bash
python3 scripts/validate.py
```

## Research notes

- [GitHub Copilot agent skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills) use the Agent Skills format and document per-surface discovery locations.
- [GitHub Copilot plugin creation](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating) supports a shared `skills/` directory and can discover `.claude-plugin/marketplace.json`.
- [Claude Code skills](https://code.claude.com/docs/en/skills) use `SKILL.md` and support personal, project, plugin, and managed locations.
- [Claude Code plugins](https://code.claude.com/docs/en/plugins) use `.claude-plugin/plugin.json`; [plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) use `.claude-plugin/marketplace.json`.
- [OpenAI Codex skills](https://developers.openai.com/codex/build-skills) use `SKILL.md`; [Codex plugins](https://developers.openai.com/codex/build-plugins) use `.codex-plugin/plugin.json` and a Codex marketplace catalog.
- The common skill format is documented by the [Agent Skills specification](https://agentskills.io/specification).

## Design choice

This repository is a marketplace containing one plugin rather than making the repository root itself the plugin. That leaves room to add separate plugins later while preserving one install source for each host.
