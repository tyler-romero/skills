# Responsive Mobile Variants & Web Integration

## 1. When to Create a `-mobile` Variant

Create a `<name>-mobile.{excalidraw,png}` variant whenever a figure is wide (`> 1000px`) and is embedded in a responsive web page or blog where scaling it down to a `375px`-wide phone screen would make text cramped or illegible:

| Desktop Layout | Mobile Transformation Pattern | Target Mobile Width |
| --- | --- | --- |
| **`1×2` side-by-side panels** | **`2×1` vertical stack** (top panel at `y0=0`, bottom panel at `y0≈560–665`) | `~640–700px` |
| **`1×3` side-by-side panels** | **`3×1` vertical stack** (`y0 = 0, 510, 1020`) | `~620–680px` |
| **`2×2` wide grid** (`~1350px` wide) | **Compact `2×2` grid** with narrower panels (`PW=350, PH=210`), tighter gaps, and bumped font sizes (`22–30px`) | `~840–900px` |
| **5-column horizontal table** (e.g., 3 draws + 2 averages) | **2-tier layout**: 3 draw columns on top tier (`MCOL = [25, 255, 485]`), horizontal rule, 2 summary columns on bottom tier (`ACOL = [90, 395]`) | `~660–700px` |
| **Wide horizontal timeline / swimlanes** | Move lane headers ("trainer", "sampler") **above** their lanes instead of in a wide left margin; tighten step widths and wrap right-hand labels onto 2 lines | `~820–920px` |
| **Wide 2-box loop diagram** | Narrow the gap between boxes (`~200px`), wrap middle annotations onto 2 lines, and tuck right-edge self-loop arrows closer to the box | `~880–940px` |

### When In-Place Tightening Is Better Than a Separate `-mobile` File
If a single-panel figure is only wide because of generous horizontal spacing or small fonts, tighten the primary layout in place (`~750–900px` wide with `24–32px` fonts) so a single asset works cleanly at both desktop and mobile widths.

---

## 2. Embedding Figures in Markdown & HTML

### A. Standard Markdown (READMEs, Docs, Single-Column Posts)
```markdown
![Descriptive alt text explaining the visual structure and takeaway.](path/to/diagram.png)
```

### B. Responsive HTML `<picture>` (Desktop + Mobile Variant)
When embedding in raw HTML or Markdown without a build-time `<picture>` transform, wire `<name>-mobile.png` explicitly with a `<source media="(max-width: 760px)">` tag:

```html
<picture>
  <source media="(max-width: 760px)" srcset="path/to/diagram-mobile.png">
  <img src="path/to/diagram.png" alt="Detailed alt text explaining the figure.">
</picture>
```

### C. Static Sites with Automatic `-mobile` Discovery (e.g., Eleventy)
Some static sites (such as Eleventy blogs with an image post-processing transform) automatically check if `<name>-mobile.<ext>` exists alongside `<name>.<ext>` on disk and inject `<source media="(max-width: 760px)">` into the generated `<picture>` tag at build time:

- In those repositories, reference **only** `<name>.png` in the Markdown or `<figure class="fullwidth">` tag and commit all four files (`<name>.excalidraw`, `<name>.png`, `<name>-mobile.excalidraw`, `<name>-mobile.png`).
- For margin-note or sidenote figures on Tufte/sidenote-style sites, target `~460–650px` canvas width so the figure fits cleanly in the margin column on desktop and inline on mobile.
