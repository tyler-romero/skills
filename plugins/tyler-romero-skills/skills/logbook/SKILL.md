---
name: logbook
description: Read, search, summarize, initialize, or update Tyler's local logbook for recorded work history and experiment tracking. Use when the user explicitly mentions the logbook, work or session history, an experiment tracker or experiment status, pending experiment follow-ups, or asks to log completed work. Do not trigger from generic requests such as "what is running" or "remind me" without logbook or experiment context.
---

# Logbook

Manage a local logbook containing daily work entries and cross-session experiment status.

## Resolve the logbook location

Resolve `<logbook>` in this order:

1. A path explicitly supplied by the user.
2. `~/.cache/agent-skills/logbook/`.

Expand `~` before using the path. If the directory does not exist, explain that no logbook was found and offer to initialize it. When the user asks to initialize it, locate this skill's directory from the loaded `SKILL.md` path and run:

```bash
uv run python <logbook-skill-directory>/scripts/init_logbook.py
```

Pass `--logbook-dir <path>` when the user selected a non-default location. The initializer creates only missing files and never replaces existing content.

## Structure

```text
<logbook>/
├── README.md          # Local conventions and schema reference
├── experiments.md     # Cross-day experiment status table
└── daily/
    └── YYYY-MM-DD.md  # Daily logs using the user's local date
```

Treat `experiments.md` as a Markdown table with this schema:

| Column | Meaning |
| --- | --- |
| Experiment | Exact job or run name; this is the row identity |
| Status | `🟡 running`, `⏳ waiting`, `🟢 completed`, or `🔴 blocked` |
| Started | Local calendar date as `YYYY-MM-DD`, or `—` when unknown |
| Last checked | ISO 8601 timestamp with UTC offset, or `—` when never verified |
| Source | Where the latest status came from, such as `logbook`, `yolo`, `Datadog`, or `Neptune` |
| Next check | Concrete follow-up time or condition, or `—` |
| Notes | Brief context needed by a future agent |

Keep one row per exact experiment name. When updating a row, match the complete `Experiment` value, preserve `Started`, and change only fields supported by new evidence. Never silently normalize, abbreviate, or rename experiment names. Add a new row when the observed name differs.

## Date and freshness rules

- Use the user's configured timezone. If none is available, use the system's local timezone and state that assumption.
- Select the daily filename and `HH:MM` heading from that timezone.
- Interpret “last week” as the previous Monday-through-Sunday calendar week and “past week” as the trailing seven days. State the absolute date range used.
- Record `Last checked` as an ISO 8601 timestamp including the UTC offset.
- Distinguish recorded status from live status. Never present a logbook entry as current live state without checking an external source.

## Operations

### Check recorded experiment status

1. Read `<logbook>/experiments.md`.
2. Report all rows, or match the exact experiment name requested by the user.
3. Label the result **Recorded status** and include its `Last checked` value.
4. For `🟡 running` or `⏳ waiting` rows, offer a live health check when monitoring tools may be available.

### Review recent activity

1. List dated files in `<logbook>/daily/`.
2. Read the most recent three to five files, or the requested date range.
3. State the absolute date range covered.
4. Summarize concisely, grouping related entries by topic or experiment when useful.

### Search for a topic

1. Search `<logbook>/daily/` and `<logbook>/experiments.md` using the user's term as a fixed string by default.
2. Present matching entries with their dates and source filenames.
3. Say clearly when there are no matches.

### Update the logbook

At the end of a session or when explicitly requested:

1. Read the target daily file first to avoid adding a duplicate entry.
2. Append to `<logbook>/daily/YYYY-MM-DD.md`, creating it when absent.
3. Use this format and omit fields that do not apply:

   ```markdown
   ## HH:MM — Short Title

   **What**: Brief description of what was done
   **Experiments**: Exact job names launched or checked
   **Files**: Key files created or modified
   **Status**: 🟢 done | 🟡 in-progress | 🔴 blocked | ⏳ waiting
   **Next**: Follow-up actions or things to check later
   ```

4. Update the matching `experiments.md` row when an experiment was launched, checked, blocked, or completed. Follow the schema and exact-name rules above.

### Remind about pending items

1. Read `experiments.md` for `🟡 running` or `⏳ waiting` rows.
2. Read the last two or three daily logs for `**Next**` items.
3. Compile likely follow-ups and include the recorded date or `Last checked` timestamp for each.
4. Do not imply that recorded items remain pending if their live state was not checked.

### Check live experiment health

Read [references/experiment-monitoring.md](references/experiment-monitoring.md) when the user requests current metrics, health, or live status. Follow its tool-discovery and graceful-degradation workflow.

## Important rules

- Preserve exact experiment names as shown by the source system so they remain searchable.
- Keep entries concise but complete enough for an agent with no prior context.
- Never delete daily entries. Append new entries and update only the matching experiment table row.
- Always identify whether a reported status is recorded or live and when it was last verified.
