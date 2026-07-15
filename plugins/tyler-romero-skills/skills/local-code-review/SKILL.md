---
name: local-code-review
description: Review local changes or a remote pull request and report findings only in the current conversation. Use when the user asks to review code, review local changes, or review a PR without posting comments, submitting a review, pushing commits, or modifying the pull request.
---

# Local Code Review

Keep the review local: inspect code and report findings in the conversation without changing the reviewed code or any remote pull request.

## Safety boundaries

- Do not edit source files, commit, push, or switch the current branch.
- Do not call commands or tools that post PR comments, submit reviews, request changes, approve, merge, close, label, or otherwise modify a pull request.
- Do not use `gh pr checkout` in the user's working tree.
- Use read-only repository, Git, and GitHub operations. Run existing tests or static checks only when they materially improve confidence and do not require source changes.

## Choose the review target

For local changes:

1. Inspect `git status --short`.
2. Read both `git diff` and `git diff --cached` as applicable.
3. Include untracked files that are part of the requested change.

For a remote pull request:

1. Read its description, metadata, changed-file list, and checks with read-only `gh pr view` or equivalent API calls.
2. Read the patch with `gh pr diff` or equivalent read-only retrieval.
3. Retrieve additional file context through read-only API calls when the patch is insufficient. Do not check the PR out over the user's current branch.

Read repository guidance such as `AGENTS.md`, `CLAUDE.md`, contribution instructions, and relevant tests before judging project conventions.

## Review priorities

Focus on actionable issues introduced by the change:

1. Correctness and broken behavior.
2. Security, privacy, and unsafe side effects.
3. Data loss, concurrency, and error-handling risks.
4. Missing or incorrect tests for meaningful behavior.
5. Maintainability problems that materially raise future defect risk.

Avoid style-only feedback unless it violates an explicit repository rule or hides a real defect.

## Report

Lead with findings ordered by severity. For each finding, include:

- Severity and a concise title.
- The affected file and tight line range when available.
- Why the behavior is wrong or risky.
- A concrete failure scenario.
- The smallest useful direction for fixing it.

After findings, list unresolved questions or assumptions, then give a short change summary. If no actionable findings exist, say so explicitly and mention any residual testing or context gaps.

Never publish the report to the pull request. Return it only in the current conversation.
