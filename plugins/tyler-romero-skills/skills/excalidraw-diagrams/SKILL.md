---
name: excalidraw-diagrams
description: "Create, edit, render, and visually verify hand-drawn Excalidraw diagrams (.excalidraw + .png), responsive mobile diagram variants (<name>-mobile.{excalidraw,png}), and animated Excalidraw GIFs (.gif). Use when asked to create or update Excalidraw diagrams, conceptual architecture figures, multi-panel plots, computational graphs, or animated Excalidraw figures in any repository or document."
---

# Excalidraw Diagrams & Animated GIFs

Create, edit, render, and visually verify hand-drawn Excalidraw diagrams (`.excalidraw` + `.png`), responsive mobile variants (`<name>-mobile.{excalidraw,png}`), and animated Excalidraw GIFs (`.gif`) with an "annotated hand-drawn notes on a technical manuscript" aesthetic.

## Locate the Bundled Scripts

Resolve this skill's directory from the loaded `SKILL.md` path, then set:

```bash
SKILL_DIR="<excalidraw-diagrams-skill-directory>"
```

All bundled scripts run from any working directory without requiring repository-local dependencies:

- [`scripts/excal.py`](./scripts/excal.py): Python `Scene` helper and color palette for authoring `.excalidraw` JSON in output-pixel coordinates.
- [`scripts/render.mjs`](./scripts/render.mjs): Headless Chrome renderer (`@excalidraw/excalidraw@0.18.1` `exportToBlob`) that works with local `puppeteer` or a zero-dependency Chrome CDP fallback.
- [`scripts/make_gif.py`](./scripts/make_gif.py): Animated GIF assembler with union bounding-box cropping and exact RGB nearest-neighbor palette quantization.

---

## Core Principles

1. **Programmatic authoring for precision**: Author diagrams in Python using the `Scene` helper ([`scripts/excal.py`](./scripts/excal.py)) rather than hand-placing raw JSON coordinates. Coordinates and font sizes are authored in **output pixels** and divided by `unit = 1.5` on save (`exportScale: 1.5`), so Excalidraw's standard `1 / 2 / 4` stroke widths look heavier and more hand-drawn relative to text.
2. **Keep `.excalidraw` source paired with rendered `.png` output**: Whenever saving static diagrams to a repository or deliverable folder, keep both `<name>.excalidraw` and `<name>.png` together so scenes remain editable and inspectable.
3. **Transparent PNGs by default**: Render static `.excalidraw` scenes with `exportBackground: false` (`exportPadding: 16`) so the transparent PNG sits directly on white (`#ffffff`), warm cream (`#fef9ed`), or tinted surfaces without a rectangular bounding box. Set `BG=#ffffff` (or `EXPORT_BG=1`) only when an opaque background is explicitly needed.
4. **Accurate Virgil text widths (`0.49 * size`)**: `@excalidraw/excalidraw`'s `exportToBlob` trusts `element.width` stored in the JSON instead of re-measuring DOM text. Always compute text width as `max(len(line) for line in lines) * size * 0.49` for Virgil (`fontFamily: 5`) to prevent 100–300px of phantom right-edge whitespace on left-aligned labels.
5. **Responsive mobile variants when targeting narrow viewports**: Wide multi-panel horizontal figures (`1×3` or `1×2` rows, wide timelines, dense multi-column charts) embedded in responsive web pages or blogs can be paired with `<name>-mobile.{excalidraw,png}` re-laid out for mobile screens (`≤ 760px`).

---

## Procedure

### 1. Choose the Figure Type, Output Path, & Layout Target

Determine where the user or target repository stores figures (for example, an explicit path requested by the user, the project's existing image/assets directory, or a scratch directory if exploring). Before writing code, choose the canvas width target (see [responsive & web integration reference](./references/responsive-and-web-integration.md)):

- **Standard single-column / README / document figure**:
  - Target canvas width: `~850–1150px` in output pixels.
  - Fits comfortably on both desktop and mobile when single-panel.
- **Wide / full-width multi-panel figure**:
  - Target desktop canvas width: `~1150–1500px`.
  - Add a companion `<name>-mobile.{excalidraw,png}` (`~640–920px` wide) when embedding in a responsive web page or blog where side-by-side panels (`1×2`, `1×3`), wide horizontal chains, or small annotations would shrink below legibility on a `375px` phone screen.
- **Compact sidebar / margin-note figure or animated GIF**:
  - Target canvas width: `~460–650px` (compact vertical or square aspect ratio).

### 2. Author the Scene in Python

Import `Scene` and palette constants from [`scripts/excal.py`](./scripts/excal.py) by adding `"$SKILL_DIR/scripts"` to `PYTHONPATH` (or `sys.path`). Follow the [scene authoring and style reference](./references/scene-authoring-and-style.md):

```bash
PYTHONPATH="$SKILL_DIR/scripts" python3 build_diagram.py
```

- Use `Scene(seed=<int>, rough=2)` for the signature sketchy hand-drawn feel (`rough=1` for plotted data curves, `rough=0` for faint reference gridlines or axes).
- Use `fontFamily: 5` (Virgil) exclusively. Keep text sizes between `20` and `40` output pixels (`30–38` for panel titles, `24–28` for subtitles and body labels, `20–24` for axis ticks and secondary notes).
- Use the established pigment palette:
  - Ink / neutral: `INK = "#1e1e1e"`, `DARK = "#495057"`, `GRAY = "#868e96"`, `RULE = "#ced4da"`, `FAINT = "#e9ecef"`
  - Blue (primary / policy $p$): stroke `#1971c2`, fill `#a5d8ff` (or `#e7f5ff`)
  - Orange (secondary / sampler $q$): stroke `#e8590c`, fill `#ffd8a8` (or `#fff4e6`)
  - Green (positive / reward / target): stroke `#2f9e44`, fill `#b2f2bb`
  - Red (negative / error / drop): stroke `#e03131`, fill `#ffc9c9`
  - Violet (shift / centering / bypass): stroke `#7048e8`, fill `#e5dbff`
  - Teal (signal vector): `#0c8599`
  - Yellow / Amber (highlight / cap): fill `#ffec99`, stroke `#f08c00` or `#e67700`
- Use `fill="hachure"` for large conceptual boxes/containers and shaded regions, and `fill="solid"` for bar-chart bars, token chips, data points, and small callout pills.
- Use typographic minus `−` (`\u2212`), multiplication `×`, middot `·`, and Unicode subscripts/superscripts (`θ₀, θ₁, 𝟏ₐ, s̄`) since Excalidraw text elements do not render LaTeX.

### 3. Render `.excalidraw` to PNG

Run [`scripts/render.mjs`](./scripts/render.mjs) to render one or more `.excalidraw` files (or a directory of `.excalidraw` frames) via `@excalidraw/excalidraw@0.18.1` (`exportToBlob`) in headless Chrome:

```bash
node "$SKILL_DIR/scripts/render.mjs" path/to/<name>.excalidraw
```

Key rendering settings supported by `render.mjs`:
- `exportBackground: false` by default (`EXPORT_BG=1` or `BG=#ffffff` / `BG=#fef9ed` to export an opaque background)
- `PADDING=16` (default `exportPadding: 16`)
- `SCALE=1.5` (defaults to `scene.appState?.exportScale ?? 1.5`)

### 4. Check Alpha Bounding-Box Margins & Label Collisions

Immediately after rendering a transparent PNG, check the alpha channel bounding box using Python (`PIL.Image`) to confirm all four margins (`L`, `T`, `R`, `B`) are balanced (`~24px` at `scale=1.5` with `exportPadding: 16`, or `~20–50px` overall) and no phantom text width is stretching the right margin:

```bash
python3 -c '
from PIL import Image
import sys
for p in sys.argv[1:]:
    im = Image.open(p)
    l, t, r, b = im.getchannel("A").getbbox()
    print(f"{p}: {im.size[0]}x{im.size[1]}  margins L={l} T={t} R={im.size[0]-r} B={im.size[1]-b}")
' path/to/<name>.png
```

If `R` (right margin) is much larger than `L` (e.g., `R > 60px`), a left-aligned text element has an overestimated `width` or an invisible element extends past the right edge. Then **view the rendered PNG directly** with the image viewer tool to inspect for overlapping labels, arrows cutting through text, or cramped spacing.

### 5. Create Mobile Variants When Needed

If the figure is wide (`1×2`, `1×3`, multi-column table/chart, or timeline) and targets a responsive web page or blog where text would look small on a `375px` mobile viewport:

1. Generate `<name>-mobile.excalidraw` and render `<name>-mobile.png`.
2. Re-layout rather than merely scaling down (see [responsive & web integration reference](./references/responsive-and-web-integration.md)):
   - Convert `1×2` or `1×3` horizontal panels into `2×1` or `3×1` vertical stacks (`~580–680px` wide).
   - Convert `2×2` wide grids into compact `2×2` grids (`~800–880px` wide) with larger `22–30px` labels.
   - Convert 5-column horizontal tables (e.g., 3 draws + 2 averages) into a **2-tier layout**: 3 draw columns on top, a horizontal divider, and 2 summary columns below (`~660–700px` wide).
3. Wire into the page using `<picture>` (`<source media="(max-width: 760px)" srcset="...-mobile.png">`), or rely on the site's build transform if the repository automatically pairs `<name>-mobile.png` with `<name>.png`.

### 6. Build Animated Excalidraw GIFs (When Applicable)

When creating an animated diagram (such as a trajectory, state machine, or step-by-step algorithm animation), follow the [animated GIFs and verification reference](./references/animated-gifs-and-verification.md):

1. **Lock export bounds**: Place a single transparent bounding rectangle (`stroke="transparent", bg="transparent", roundness=None`) around the full canvas in every frame so `exportToBlob` never jitters or crops differently as elements move.
2. **Keep element count & seeds stable**: Instantiate `Scene(seed=<fixed_int>, rough=2)` with the same seed on every frame and draw elements in a fixed order (using `opacity=0` instead of omitting elements that appear/disappear mid-animation) so every static shape keeps the exact same hand-drawn wobble across frames.
3. **Smooth transitions & holds**: Use cubic Hermite easing `ease(u) = u * u * (3 - 2 * u)` for intermediate motion frames (`~90–110ms` per frame) and longer holds (`450–2500ms`) on key states and the final frame. Write per-frame durations (in ms) to `frames.json`.
4. **Render & assemble with `make_gif.py`**:
   - Batch-render `frame_NNN.excalidraw` to transparent `frame_NNN.png` using `node "$SKILL_DIR/scripts/render.mjs" /path/to/frames_dir`.
   - Run [`scripts/make_gif.py`](./scripts/make_gif.py) with `--bg` matching the target page background (`#fef9ed` for warm cream paper, `#ffffff` for white pages/READMEs) to composite frames, crop to the union bounding box across all frames, and quantize to a 48-color palette with exact Euclidean nearest-neighbor lookup:
     ```bash
     python3 "$SKILL_DIR/scripts/make_gif.py" /path/to/frames_dir path/to/<name>.gif --bg "#fef9ed"
     ```

### 7. Verify in Context

1. Always inspect the rendered `.png` or `.gif` directly with the image viewer tool to verify typography, margins, alignment, and arrow routing.
2. If the figure is embedded in a website, blog, or document with a build/preview pipeline, run the project's build/check command and inspect the rendered page at desktop (`1400×900`) and mobile (`375×812`) viewports to confirm legibility and background blending.
