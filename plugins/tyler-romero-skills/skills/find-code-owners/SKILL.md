---
name: find-code-owners
description: Identify likely code owners, maintainers, domain experts, or reviewers for files and changes using Git history, recency, commit frequency, and cross-file coverage. Use when the user asks who owns code, who knows a file or directory, who should review a change, who a good owner would be, or whom to add to CODEOWNERS or OWNERS.
---

# Find Code Owners

Recommend people with demonstrated, recent knowledge of the affected code. Distinguish official ownership policy from historical expertise.

## Safety boundaries

- Use read-only Git and GitHub operations by default.
- Do not edit `CODEOWNERS`, `OWNERS`, team files, or repository settings unless the user explicitly asks for that change.
- Do not request reviewers, assign users, or post comments unless the user explicitly asks for the external action.
- Avoid exposing private email addresses when a name or verified GitHub login is available.

## 1. Determine the target paths

For local work, use the paths supplied by the user or collect changed files from staged, unstaged, and relevant untracked changes.

For a pull request, retrieve its changed-file list and author through read-only `gh pr view` or equivalent API calls. Exclude the PR author from reviewer recommendations unless the user asks otherwise.

Group generated files, vendored code, lockfiles, and mechanical outputs separately; their commit history often identifies automation rather than true ownership.

## Delegate evidence gathering when useful

When the host supports subagents and the target spans many files or ownership boundaries, delegate the read-only evidence-gathering pass to a lower-cost or faster subagent. Give it:

- The repository and exact target paths.
- The PR author or identities to exclude.
- The command below and the scoring parameters to use.
- Instructions to inspect representative commits for the leading candidates.
- A requirement to return raw rankings, commit hashes, path coverage, and identity-mapping uncertainty rather than a polished recommendation.

Do not delegate small lookups where coordination costs more than the work. The primary agent must read the raw evidence, independently check explicit ownership policy, verify substantive commits, resolve identity ambiguity, and write the final report. Never delegate an external action such as requesting reviewers or modifying ownership configuration.

## 2. Check explicit ownership policy

Look for repository ownership sources such as:

- `.github/CODEOWNERS`
- `CODEOWNERS`
- `OWNERS` files
- Repository-specific team or ownership configuration

Report matches from these files as **official owners**. Do not claim that Git history overrides required ownership policy.

Use history to identify **recommended experts or reviewers**, resolve broad team entries, or suggest ownership where explicit policy is absent.

## 3. Rank historical candidates

Resolve this skill's directory from the loaded `SKILL.md` path and run:

```bash
uv run python <skill-directory>/scripts/rank_owners.py <path> [<path> ...]
```

Use `uv run python` for every invocation of the bundled Python script. If `uv` is unavailable, stop and tell the user that the required runner is missing rather than silently using another Python environment.

When no paths are passed, the script uses current working-tree changes. Useful options:

```bash
--half-life-days 180   # recency decay; newer commits count more
--max-commits 200      # per-path history depth
--limit 10             # number of candidates to report
--exclude <identity>   # repeat for PR author, current user, or known bots
--json                 # machine-readable output
--include-emails       # opt in only when identity disambiguation requires it
```

The script follows file renames, applies `.mailmap`, falls back to parent-directory history for new files, filters common bots, and reports each candidate's weighted score, commits, coverage, last activity, and strongest paths.

By default, output includes names and verified GitHub logins but omits email addresses. Use email output only for local identity disambiguation and do not reproduce private addresses in the final report.

## 4. Verify the evidence

Treat the ranking as evidence, not a final answer. For the leading candidates:

1. Inspect representative commits with `git log --author=<identity> -- <path>`.
2. Discount bulk formatting, generated changes, vendoring, mass renames, and one-off mechanical edits.
3. Prefer authors of substantive changes, fixes, tests, and design work in the affected area.
4. Prefer recent activity when expertise is otherwise similar.
5. For multiple files, prefer a small set whose combined history covers every meaningful ownership boundary.
6. Map commit identities to GitHub logins using noreply addresses, `.mailmap`, commit metadata, or read-only GitHub lookups. State uncertainty when the mapping is not verified.

Do not recommend an inactive or unreachable person solely because they dominate old history. If activity status is unavailable, describe the recommendation as historical.

## 5. Assess confidence

- **High:** recent substantive exact-file history, repeated contributions, and broad coverage of the requested paths.
- **Medium:** good directory-level or older exact-file history, with some uncertainty about current responsibility.
- **Low:** sparse history, mostly mechanical commits, ambiguous identities, or only broad parent-directory evidence.

For new files, infer expertise from the closest relevant directory, neighboring modules, tests, and the authors of the change that introduced the surrounding abstraction.

## 6. Report

Return:

1. **Official owners:** policy-derived owners and the files or rules that selected them.
2. **Recommended experts:** ranked people with concise Git-history evidence.
3. **Suggested reviewer set:** the smallest reasonable set covering the requested paths.
4. **Confidence and caveats:** identity mapping, stale history, generated files, or missing policy.

Include the commands or evidence used. Recommend reviewers by default; perform reviewer requests or ownership edits only after explicit user authorization.
