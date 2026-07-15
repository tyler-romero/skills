---
name: portable-smoke-test
description: Verify that the shared Agent Skill is installed and loaded. Use when the user asks to "run the portable skill smoke test", "test the cross-platform skill", or verify this skills plugin with a token such as "violet-otter".
---

# Portable Smoke Test

Extract the test token from the user's request. Use `violet-otter` when no token is supplied.

Reply with exactly these three lines, replacing `<token>` with the extracted token:

```text
PORTABLE_SKILL_OK
skill: portable-smoke-test
token: <token>
```

Do not add commentary, Markdown fences, or other text.
