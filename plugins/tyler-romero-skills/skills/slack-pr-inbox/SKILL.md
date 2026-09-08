---
name: slack-pr-inbox
description: Track GitHub pull-request review requests directed at the authenticated user through Slack mentions, threads, or DMs, and reconcile them with current GitHub review and PR status. Use when the user asks for their PR review inbox, outstanding reviews, review requests from Slack, who asked them to review PRs, or whether those requests are complete.
---

# Slack PR Inbox

Build a read-only inbox of pull-request review requests directed at the authenticated user in Slack, then reconcile each request with GitHub.

## Safety boundaries

- Use only read operations in Slack and GitHub.
- Never post, react, edit, or delete Slack content.
- Never submit a review, comment, request reviewers, merge, close, edit, or otherwise modify a pull request.
- Do not expose Slack or GitHub credentials, tokens, cookies, private email addresses, or unrelated private conversation content.

## Choose the time window

Use the window supplied by the user and state its absolute dates. Interpret dates in the user's configured timezone.

If the user gives no window, use the trailing seven calendar days. Do not silently expand beyond an explicit lower bound such as “since last Thursday.” Include requests at the lower-bound timestamp.

## Find candidate requests in Slack

1. Resolve the authenticated Slack user's ID and display name using the available read-only profile or authentication-status capability.
2. Search all accessible conversations within the window for:
   - Direct mentions of the authenticated user.
   - `PTAL`, `TAL`, `review`, `rereview`, `approve`, `take a look`, and similar review-request wording.
   - Direct messages to the user containing review-request wording, even when no explicit mention appears.
3. Read the surrounding thread or DM history when the matching message does not itself contain the PR URL, title, or original request.
4. Keep a candidate only when the context establishes an actual request for the user to review a GitHub pull request. Exclude general discussion, automated notifications, status updates, requests aimed only at someone else, non-PR uses of “review,” and incidental PR links.
5. Extract the repository and PR number from the GitHub URL. If the context contains only a bare PR number, infer the repository only when it is unambiguous; otherwise report the unresolved request separately instead of guessing.

For each request, retain:

- The first request timestamp and permalink.
- Later explicit reminders or rereview requests, with their timestamps and permalinks.
- The person making the request, which may differ from the PR author.
- Whether the request named the user alone or allowed an alternate reviewer, such as “Tyler or Tanmay.”

Deduplicate by repository and PR number, not by Slack message. A later reminder is part of the same inbox item but may reset its completion status.

## Read GitHub state

Verify that `gh` is authenticated and obtain the current GitHub login:

```bash
gh auth status
gh api user --jq .login
```

For each PR, use read-only `gh pr view` or GitHub GET requests to retrieve its title, URL, state, draft status, merge and close timestamps, review requests, and submitted reviews. Fetch enough review detail to identify the reviewer, state, submission time, and review URL.

Exclude automated reviewers, including Copilot and accounts ending in `[bot]`, when deciding whether a human fulfilled a request.

## Determine completion status

Compare GitHub events with the latest applicable Slack request or reminder:

- **Done — reviewed by you:** the authenticated GitHub user submitted `APPROVED`, `CHANGES_REQUESTED`, or `COMMENTED` after the latest request. Preserve the review result in the note.
- **Done — resolved:** the PR merged after the request. State whether the user reviewed it, an explicitly allowed alternate covered it, or it resolved without their review.
- **Covered by alternate:** the Slack request explicitly allowed another reviewer and that person submitted a qualifying review. Do not infer delegation merely because somebody else reviewed.
- **Cancelled:** the PR closed without merging. Mention when Slack context shows that the requestor withdrew it.
- **In progress:** the PR remains open and the user acknowledged in Slack that they were taking it, or GitHub exposes an unsubmitted pending review from the user.
- **Outstanding:** the PR remains open and no completion or in-progress signal applies.

A reminder or explicit rereview request that occurs after the user's last submitted review makes the item outstanding again unless the PR is already merged or closed. A review submitted before the request does not complete that request.

Treat a draft PR as open; add `draft` to the status rather than assuming it is not actionable.

## Report

Lead with the active inbox: `Outstanding` and `In progress`, newest request first. Follow with completed, covered, cancelled, merged, or closed items.

Use a compact table with:

| Requested | Requestor | PR | Status |
| --- | --- | --- | --- |

- Link the request timestamp to the exact Slack message.
- Show the user's local date and time, including the timezone abbreviation when useful.
- Link the PR using its number and current title.
- Link later reminders beside the original request.
- Make status wording explicit about whether the user reviewed it, an alternate covered it, it merged, or it closed.

State the absolute date range searched, note any inaccessible conversations or result limits that could make the inbox incomplete, and list the primary Slack searches and `gh` read commands used.

Do not create a persistent file, recurring automation, Slack reminder, or external notification unless the user separately asks for one.
