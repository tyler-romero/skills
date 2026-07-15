---
name: chrome-cdp
description: Launch or control a dedicated Google Chrome debugging profile through the Chrome DevTools Protocol using bundled dependency-free Node.js scripts, pausing for the user to authenticate manually before automation begins. Use when the user asks to operate a logged-in web app, inspect the DOM, take screenshots, click, type, scroll, upload files, download or save PDFs, or automate browser UI and no safer API, MCP connector, or native browser tool is available.
---

# Chrome CDP

Launch or reuse a visible Chrome session over the local Chrome DevTools Protocol (CDP). Use a persistent debugging profile so the user can authenticate manually once and reuse that session later.

## Prefer safer interfaces

Use a purpose-built API, CLI, MCP connector, or native browser tool when one exists. Use this skill when browser UI automation is necessary or when an authenticated session is available only in Chrome.

## Safety boundaries

- Connect only to the loopback debugging endpoint. Never expose the CDP port to the network.
- Treat the browser as the user's hands. Stay within the requested task and stop on surprising state.
- Require explicit, current approval immediately before submitting, sending, paying, deleting, publishing, confirming, or performing another outward-facing or irreversible action.
- Keep emails, forms, expenses, and similar work in draft state unless the user explicitly approves the final action.
- Keep screenshots and DOM extracts containing personal, financial, or authentication data in temporary session storage. Do not echo or persist more than necessary.
- Verify the target tab by title and URL before every consequential sequence.
- Never inspect, screenshot, type into, or otherwise interact with login, password-manager, MFA, security-key, or CAPTCHA interfaces. Pause and hand control to the user.

## Prerequisites

- Node.js 22 or later for built-in `fetch` and `WebSocket`.
- Google Chrome installed locally.
- The user available to complete login, MFA, CAPTCHA, and other authentication steps manually.

Chrome 136 and later ignore `--remote-debugging-port` for the default Chrome data directory. Use a dedicated, persistent debugging profile.

## Locate the bundled scripts

Resolve this skill's directory from the loaded `SKILL.md` path, then set:

```bash
S="<chrome-cdp-skill-directory>/scripts"
```

The bundled scripts require no npm installation:

- `launch-chrome.js`: reuse a live endpoint or launch the dedicated debugging profile.
- `cdp.js`: core target, screenshot, navigation, PDF, input, upload, download, and evaluation commands.
- `safeshot.js`: screenshot with timeout and dialog recovery.
- `safeeval.js`: JavaScript evaluation with timeout.
- `findxy.js`: find visible text and return its CSS-pixel center.

## Launch and authentication handoff

Run the launcher yourself:

```bash
node "$S/launch-chrome.js"
```

To open a specific public starting page:

```bash
node "$S/launch-chrome.js" --url "https://example.com"
```

The launcher reuses an active loopback CDP endpoint or starts Chrome with the persistent profile at `$CHROME_CDP_PROFILE` (default `~/.chrome-cdp-profile`). Set `CDP_PORT` to override port `9222`.

After launching:

1. Tell the user that the dedicated Chrome window is ready.
2. Ask the user to take control, navigate as needed, and complete all login, MFA, CAPTCHA, consent, and password-manager interactions manually.
3. Pause. Do not inspect tabs or issue CDP commands while authentication is in progress.
4. Resume only after the user explicitly says authentication is complete and hands control back.
5. Verify the endpoint, then list tabs and confirm the intended title and URL with the user when ambiguous.

Never ask the user to paste credentials or authentication codes into the conversation.

## Automation workflow

1. Verify the endpoint with `curl --fail --silent http://localhost:${CDP_PORT:-9222}/json/version`.
2. List tabs with `node "$S/cdp.js" targets`.
3. Select the exact page target and retain its id in `TAB`.
4. Activate the tab before screenshots or evaluation:

   ```bash
   curl --fail --silent "http://localhost:${CDP_PORT:-9222}/json/activate/$TAB" >/dev/null
   ```

5. Capture the current state with `node "$S/safeshot.js" "$TAB" shot.png` and inspect the image.
6. Prefer `findxy.js` or DOM inspection over guessing coordinates.
7. Perform one action, wait for the UI to settle, and capture or inspect the live DOM again.
8. Before a consequential action, restate the exact action and obtain current user approval.

Clicks use viewport-relative CSS pixels, not screenshot pixels. Always query `innerWidth`, `innerHeight`, and `devicePixelRatio` before converting visual coordinates.

Read [references/operations.md](references/operations.md) for the full command reference, coordinate conversion, upload patterns, DOM evaluation examples, timeout recovery, and PDF workflows.
