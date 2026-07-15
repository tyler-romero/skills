---
name: handoff
description: Create a concise, secure handoff document so a fresh agent can continue the current task without reconstructing the conversation. Use only when the user explicitly asks for a handoff, continuation document, session transfer, or context package for another agent.
---

# Handoff

Create a self-contained continuation document for a fresh agent.

Include:

- Current objective and intended outcome.
- Completed work and important decisions.
- Current repository, branch, and working-tree state when relevant.
- Remaining work in execution order.
- Verification already performed and commands still worth running.
- Constraints, assumptions, blockers, and known risks.
- Relevant files, commits, issues, pull requests, and other artifacts.
- Suggested skills or tools for the next agent.

Reference existing artifacts by path or URL instead of duplicating their contents. Omit stale conversational detail that does not affect continuation.

Redact credentials, tokens, personal data, and other sensitive information. Never copy secrets into the handoff.

If the user specifies what the next session will focus on, prioritize that context. Save the document in the operating system's temporary directory rather than the current workspace. If file creation is unavailable, return the complete handoff inline instead.

Report the saved path and a one-sentence description of what the handoff prepares the next agent to do.
