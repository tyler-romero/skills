# Scene Authoring and Visual Style

## 1. The `unit = 1.5` Coordinate System

`Scene(seed=7, unit=1.5, rough=2)` in [`scripts/excal.py`](../scripts/excal.py) lets you author every coordinate (`x, y, w, h`) and `fontSize` directly in **output pixels**:

- When `scene.save(path)` runs, all geometry (`x`, `y`, `width`, `height`, `points`) and `fontSize` are divided by `unit = 1.5`, while `appState.exportScale` is saved as `1.5`.
- Excalidraw only supports discrete `strokeWidth` steps (`1`, `2`, `4`). Dividing scene geometry by `1.5` while keeping `sw=1`, `sw=2`, or `sw=4` makes strokes `1.5×` heavier relative to text and boxes, producing a warm, hand-sketched pen weight.
- When `render.mjs` exports the scene with `scale = scene.appState.exportScale` (`1.5`), the rendered PNG dimensions match your authored pixel coordinates (plus `2 * exportPadding * scale` = `48px` total margin when `exportPadding: 16`).

---

## 2. The Virgil `0.49` Text Width Rule (Critical)

`@excalidraw/excalidraw`'s `exportToBlob` computes the exported canvas bounding box from the `x`, `y`, `width`, and `height` fields stored in the `.excalidraw` JSON — it **does not** re-measure rendered text in the DOM.

- If you estimate text width with `0.58 * size` or `0.62 * size`, left-aligned text near the right edge of a figure will inflate the scene's bounding box by 100–300px of empty transparent space on the right (`R >> L`).
- For Virgil (`fontFamily: 5`), the empirical average glyph width is **`0.49 * size`**:
  ```python
  lines = s.split("\n")
  w = max(len(line) for line in lines) * size * 0.49
  h = len(lines) * size * 1.25
  ```
- For `align="center"`, pass the horizontal center `x`; `Scene.text` shifts `x -= w / 2`.
- For `align="right"`, pass the right anchor `x`; `Scene.text` shifts `x -= w`.
- When binding a centered label inside a shape (`s.rect(x, y, w, h, label="...", size=28)`), `Scene.shape` automatically binds the text element to the container's `boundElements`.

---

## 3. Color Palette & Fill Conventions

By default, diagrams are exported with a transparent background (`exportBackground: false`) so they sit directly on white (`#ffffff`), warm cream (`#fef9ed`), or lightly tinted surfaces without a rectangular bounding box. Never place an opaque background rectangle behind the whole figure unless a self-contained card is explicitly desired.

| Semantic Role | Stroke / Text Hex | Fill Hex | Typical Usage |
| --- | --- | --- | --- |
| Primary ink | `#1e1e1e` (`INK`) | — | Titles, primary labels, axes, main arrows |
| Secondary dark | `#495057` (`DARK`) | — | Sub-descriptions inside boxes, baseline curves |
| Muted / annotations | `#868e96` (`GRAY`) | `#f1f3f5` (`TOKEN_FILL`) | Subtitles, axis labels, tick labels, dashed reference lines |
| Faint rules / grid | `#ced4da` / `#dee2e6` / `#e9ecef` | `#e9ecef` | Horizontal gridlines, dividers, background histograms |
| Primary / Blue | `#1971c2` (`BLUE_INK`) | `#a5d8ff` (`BLUE`) / `#e7f5ff` | Primary system/policy $p$, main curves, probability bars |
| Secondary / Orange | `#e8590c` (`ORANGE`) | `#ffd8a8` (`ORANGE_FILL`) / `#fff4e6` | Secondary system/sampler $q$, drift/rollout curves |
| Positive / Target / Green | `#2f9e44` (`DARK_GREEN`) | `#b2f2bb` (`GREEN`) | High-reward target `★`, positive delta, success block |
| Negative / Error / Red | `#e03131` (`RED`) | `#ffc9c9` (`RED_FILL`) | Error path, negative delta, dropped/rejected items |
| Shift / Bypass / Violet | `#7048e8` (`VIOLET`) | `#e5dbff` (`VIOLET_FILL`) | Centering shift, straight-through backward pass, metadata |
| Signal / Teal | `#0c8599` (`TEAL`) | `#c3fae8` (contours) | True gradient / signal vector |
| Highlight / Cap / Amber | `#f08c00` / `#e67700` | `#ffec99` (`YELLOW`) | Clipping/truncation cap, warning callouts |

### Fill Styles (`fillStyle`)
- **`fill="hachure"`** (default in `Scene`): Use for large conceptual containers (e.g., architecture blocks, banners, shaded bands). Gives a hand-shaded notebook look.
- **`fill="solid"`**: Use for bar-chart bars, token chips, small callout pills, nodes/dots on curves, and computational-graph boxes where dense text sits inside small rectangles.
- **`roundness`**:
  - `Scene.rect` defaults to `roundness={"type": 3}` (soft rounded corners).
  - Pass `roundness=None` for sharp-cornered bar chart columns, histogram bins, and table/token cells.

### Roughness (`roughness`)
- Use `Scene(seed=..., rough=2)` for most figures so boxes, dividers, and arrows have warm hand-drawn character.
- Override with `rough=1` on plotted data curves (`s.poly(pts, stroke=..., sw=2, rough=1)`) so data remains faithful.
- Override with `rough=0` on faint gridlines (`stroke="#e9ecef"`), tick marks, small circular markers, or tight orthogonal paths (`rough=0.5`).

---

## 4. Typography & Mathematical Notation

Excalidraw text elements render plain Unicode strings in Virgil (`fontFamily: 5`), **not** KaTeX.
- Always use real typographic characters:
  - Minus sign: `−` (`\u2212`), never ASCII hyphen `-` (`+1 / −1`, `−0.3`, `1ₐ − p`)
  - Multiplication: `×` (`17 × 24`)
  - Dot product / scalar multiply: `·` (`w · (𝟏ₐ − p)`)
  - Comparison / arrows: `≠`, `≈`, `≤`, `≥`, `→`, `←`
  - Subscripts & symbols: `θ₀, θ₁, θ₂, θ₃`, `₆₈, ₅₈, ₈₆`, `𝟏ₐ`, `s̄` (`s\u0304`), `★`
- Recommended font sizes (in output pixels):
  - **Main panel / figure title**: `30–38px` (`color=INK`)
  - **Subtitle / conditioning context**: `23–28px` (`color=GRAY`, placed `40–50px` below the title)
  - **Box headers / primary labels**: `28–36px`
  - **Data labels / curve annotations / captions**: `22–26px`
  - **Axis tick numbers**: `20–24px` (`color=GRAY`)
  - Never drop below `20px` on desktop or `21px` on mobile.

---

## 5. Common Diagram Archetypes

### A. Conceptual Architecture / Loop
- Two or more `hachure`-filled rounded rects (`sw=2`) connected by curved 3-point arrows (`s.arrow(p0, p_mid, p1, sw=2)`).
- Keep horizontal gaps tight (`~250–300px`) so connecting arrows don't leave vast empty whitespace in the middle of the figure.

### B. Multi-Panel Line Plots
- Load empirical or simulated curve coordinates from a `.json` file or shared Python module so desktop and mobile scripts share exact data.
- Draw axes with `s.line(..., sw=1, rough=1)` and horizontal gridlines with `s.line(..., sw=1, stroke="#dee2e6" or "#e9ecef", rough=0)`.
- Label curves directly on the canvas (`s.text(X(lx), Y(ly), label, color=color, align="center")`) rather than using a separate legend box whenever possible.

### C. Small-Multiple Bar / Logit Tables
- Use a helper `bars(sc, x0, y0, vals, ...)` that draws a baseline `s.line(x0 - 8, y0, x0 + CHART_W + 8, y0, sw=1.5, stroke=GRAY, rough=2)` and `fill="solid"`, `roundness=None` rectangles above (`y0 - h`) or below (`y0`) the zero line.
- Place numeric value labels just above positive bars (`y0 - h - 30`) and just below negative bars (`y0 + h + 4`), with category labels below the lowest negative bar (`y0 + 94`).

### D. Forward / Backward Computational Graphs
- Use solid arrows (`style="solid"`) on the left (`x - O`) for the forward pass and dashed violet/dark arrows (`style="dashed"`) on the right (`x + O`) for the backward pass.
- To show a straight-through estimator (STE) or skip connection bypassing an operation node (like `+`), route a multi-point orthogonal or curved dashed arrow around the node (`roundness=None, rough=0.5`).
