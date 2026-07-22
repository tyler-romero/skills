---
name: resolve-review-comments
description: Iteratively evaluate and resolve unresolved GitHub pull-request review threads against the PR's latest commit, recommend whether each comment should be addressed, implement approved fixes, and after separate approval commit, push, reply with the commit link, and resolve the thread. Use when the user asks to address, work through, clear, or resolve review comments or PR feedback one thread at a time.
---

# Resolve Review Comments

Process unresolved GitHub review threads serially. Preserve two approval gates for every actionable thread: one before editing and another before committing or modifying GitHub.

## Safety boundaries

- Never discard, overwrite, stage, or commit unrelated worktree changes. If they overlap the required edit, stop and ask the user how to proceed.
- Do not post a reply or resolve a still-applicable thread before the user approves the implementation.
- Resolve a stale thread without an additional approval only because invoking this workflow explicitly authorizes that step.

## 1. Identify and prepare the pull request

1. Determine the exact repository and PR. If more than one PR is plausible, ask the user to identify it.
2. Refer to a known PR as `[PR #<number>](https://github.com/<owner>/<repository>/pull/<number>)` in user-facing text.
3. Read repository guidance such as `AGENTS.md`, `CLAUDE.md`, contribution instructions, and relevant test documentation.
4. Retrieve the PR's base branch, head branch, head repository, current head SHA, changed files, and unresolved review threads using read-only `gh` commands or equivalent GitHub API calls. Follow pagination so no unresolved thread is omitted.
5. Work on the PR head branch. Fetch or check it out safely when necessary, without losing local changes. Verify that the user has push access before promising the remote steps.
6. Record existing staged, unstaged, and untracked changes so later staging can remain limited to this workflow.

Process unresolved review threads from oldest to newest unless the user requests another order. A thread, rather than each reply within it, is the unit of work.

## 2. Refresh and assess one thread

Before assessing each thread:

1. Refresh the PR metadata and current head SHA.
2. Refresh the thread. Skip it if another actor has already resolved it.
3. Read the full thread, the original diff context, the current version of the referenced file, and relevant surrounding code and tests.
4. Inspect intervening commits or related files when needed to understand whether the concern remains.

Determine semantic staleness against the latest PR head:

- Mark the thread **stale** only when the reported problem has already been fixed, the relevant code was removed, or the comment's premise is no longer true.
- Treat GitHub's `isOutdated` value as a clue, not a conclusion. A moved line or outdated diff position is not stale when the underlying problem still exists.
- Treat duplicate feedback as stale when an earlier approved fix in this workflow has already eliminated the problem.

When stale, resolve the thread through GitHub, then tell the user which thread was resolved and briefly state why it no longer applies. Do not post a reply unless the user asks. Continue to the next thread.

## 3. Recommend an action and ask for approval

For a thread that still applies, present:

- The reviewer, file and current line or symbol, and a link to the thread when available.
- A concise explanation of the concern and whether it is valid.
- A clear recommendation: address it or do not address it.
- If recommending a change, a brief implementation outline, likely files affected, and intended validation.
- If recommending no change, the technical reason and any tradeoff.

Ask for the user's decision before editing. Do not bundle decisions for several threads into one question.

If the user agrees not to address the comment, leave the thread unresolved and move to the next one. Reply to or resolve it only with separate explicit authorization.

## 4. Implement the approved recommendation

After approval to address the thread:

1. Make only the changes needed for that thread.
2. Add or update focused tests when appropriate.
3. Run the narrowest meaningful validation, expanding only when risk or repository guidance warrants it.
4. Review the resulting diff for correctness, scope, formatting, generated artifacts, and secrets.
5. If the necessary implementation materially differs from the approved outline, explain the change in scope and seek approval before continuing.
6. Present the implementation summary, tests and results, and any residual risk. Ask whether the user approves the implementation and explicitly authorizes committing it, pushing it, replying with the commit URL, and resolving this thread.

Do not commit, push, post, or resolve while waiting. If the user rejects the implementation, revise or undo only the changes made for this thread as directed, then seek approval again.

## 5. Publish an approved implementation

After the user approves the implementation:

1. Refresh the PR head and thread again. If the head changed, rebase or update safely as appropriate, then reassess whether the comment and implementation still apply. Return to an approval gate if the implementation materially changes.
2. Verify the diff contains only the approved thread's work. Stage only its files or hunks.
3. Create one new commit following the repository's commit-message conventions.
4. Push the PR head branch.
5. Verify the pushed commit's full SHA and construct its canonical URL:

   `https://github.com/<owner>/<repository>/commit/<full-sha>`

6. Reply in the review thread with exactly that URL and no other text.
7. Resolve the thread only after both the push and reply succeed.
8. Report the linked commit and successful resolution to the user.

If commit, push, reply, or resolution fails, stop the publication sequence at that point and report the failure. Never resolve a thread when the commit is not available on GitHub or the required reply was not posted.

## 6. Continue until complete

Refresh the unresolved thread list and repeat from section 2. After the final thread, summarize:

- Threads resolved as stale.
- Threads fixed, with one commit link per thread.
- Threads deliberately left unresolved and why.
- Any failures, skipped validation, or remaining user action.
