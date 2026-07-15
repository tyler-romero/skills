# Chrome CDP Operations

## Command reference

Run core commands as `node "$S/cdp.js" <command> ...`.

| Command | Purpose |
| --- | --- |
| `targets` | List page targets with id, title, and URL. |
| `shot <target> <out.png>` | Capture a screenshot and print viewport metadata. |
| `nav <target> <url>` | Navigate and wait for the page load event. |
| `pdf <target> <out.pdf>` | Print the page to PDF with backgrounds. |
| `savemail <target> <out.html>` | Save the open Gmail message body as standalone HTML. |
| `eval <target> <file.js>` | Evaluate a JavaScript file and print its returned JSON value. |
| `click <target> <x> <y>` | Click viewport-relative CSS coordinates. |
| `type <target> <text>` | Insert text into the focused element. |
| `key <target> <key>` | Dispatch `Enter`, `Tab`, `Escape`, or `Backspace`. |
| `wheel <target> <x> <y> <deltaY>` | Scroll the element under a viewport point. |
| `setdl <path>` | Set the browser download directory. |
| `filecount <target>` | Count file inputs, including pierced DOM nodes. |
| `setfile <target> <file> [index]` | Assign a file directly to a file input. |
| `chooserupload <target> <x> <y> <file>` | Intercept a file chooser and upload a file. |

Use `-` instead of a target id only when operating on the first page is unquestionably safe.

## Screenshot and coordinate loop

Prefer the timeout-guarded screenshot:

```bash
node "$S/safeshot.js" "$TAB" shot.png
```

Query the viewport before using image-derived coordinates:

```bash
printf '%s\n' '({w:innerWidth,h:innerHeight,dpr:devicePixelRatio,url:location.href,title:document.title})' > /tmp/chrome-cdp-viewport.js
node "$S/safeeval.js" "$TAB" /tmp/chrome-cdp-viewport.js
```

Three coordinate spaces may differ:

- CSS pixels: expected by CDP input commands.
- Original screenshot pixels: CSS dimensions multiplied by device pixel ratio.
- Displayed image pixels: dimensions shown by the image viewer.

Convert displayed coordinates with:

```text
CSS_x = displayed_x * CSS_width / displayed_width
CSS_y = displayed_y * CSS_height / displayed_height
```

Recalculate after scrolling, resizing, zooming, or opening a panel.

## Find elements by text

```bash
node "$S/findxy.js" "$TAB" "Submit"
node "$S/findxy.js" "$TAB" "Submit" --all
```

The result contains viewport-relative CSS centers ready for `cdp.js click`. Screenshot after clicking to confirm the result.

## Inspect visible controls

Write evaluation snippets to a temporary file. The last expression is returned by value.

```js
(() => {
  const visible = element => {
    const rect = element.getBoundingClientRect();
    const style = getComputedStyle(element);
    return rect.width > 2 && rect.height > 2 &&
      style.visibility !== 'hidden' && style.display !== 'none' &&
      rect.bottom > 0 && rect.top < innerHeight &&
      rect.right > 0 && rect.left < innerWidth;
  };
  const center = element => {
    const rect = element.getBoundingClientRect();
    return {
      x: Math.round(rect.left + rect.width / 2),
      y: Math.round(rect.top + rect.height / 2),
    };
  };
  const controls = [...document.querySelectorAll(
    'input,select,textarea,button,a,[role=button],[role=combobox]'
  )].filter(visible).map(element => ({
    tag: element.tagName.toLowerCase(),
    name: (
      element.getAttribute('aria-label') || element.innerText ||
      element.name || ''
    ).trim().slice(0, 80),
    value: (element.value || '').slice(0, 80),
    ...center(element),
  }));
  return controls.slice(0, 100);
})()
```

## Timing and stale screenshots

- Activate background tabs before capture or evaluation.
- Prefer `safeshot.js` and `safeeval.js`; inline PDF previews, JavaScript dialogs, and native file dialogs can wedge renderer calls.
- Wait after actions that trigger navigation, panels, or server round trips.
- During loading overlays, screenshots may show a stale frame. Poll the live DOM and capture again only after the loading state clears.
- Type then press `Tab` for lookup or combobox fields that require blur to commit.

Example loading-state probe:

```js
({
  waiting: /please wait|processing|loading/i.test(document.body.innerText),
  dialogs: [...document.querySelectorAll('[role=dialog]')]
    .map(element => element.innerText.slice(0, 200)),
})
```

## File upload and download

Use `chooserupload` when clicking an upload button opens a native chooser:

```bash
node "$S/cdp.js" chooserupload "$TAB" <x> <y> /absolute/path/to/file
```

Use `setfile` when a file input is directly reachable:

```bash
node "$S/cdp.js" filecount "$TAB"
node "$S/cdp.js" setfile "$TAB" /absolute/path/to/file 0
```

Set the download directory before initiating a download:

```bash
node "$S/cdp.js" setdl /absolute/path/to/downloads
```

Verify that uploaded and downloaded files are the expected files before continuing.

## Save a page as PDF

```bash
node "$S/cdp.js" pdf "$TAB" page.pdf
```

For Gmail, `savemail` extracts the visible message body before printing or conversion:

```bash
node "$S/cdp.js" savemail "$TAB" message.html
```

Treat email bodies and generated PDFs as sensitive session artifacts.

## Iframes and shadow DOM

`Runtime.evaluate` runs in the selected target's top frame. The file-input helpers pierce shadow roots and iframe documents through the DOM domain, but arbitrary content inspection may require selecting another target or explicitly traversing frames.

Do not assume that a visible iframe shares the top frame's execution context.
