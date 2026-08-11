---
name: latex-report
description: "Create polished LaTeX reports, technical reports, whitepapers, research papers, and research summaries with compiled PDFs. Use when the user asks to write, structure, typeset, compile, render, or visually verify a professional long-form document. Default to a modern single-column ML-paper style when no venue or brand format is specified, while adapting the structure and styling to the actual content."
---

# LaTeX Report

Turn source material into an evidence-backed ML research paper or technical report. Default to a single-column preprint style; use a venue template instead when the user names a conference, journal, or required format.

## 1. Establish the paper brief

Identify the paper's audience, research question, contribution, evidence, authorship, expected length, anonymity requirements, and output location. Infer low-risk details and state assumptions that affect scientific interpretation or attribution.

Choose the closest narrative as a starting point:

| Mode | Possible starting structure |
| --- | --- |
| Research paper | Abstract, introduction, related work, method, experiments, results, limitations, conclusion |
| Technical report | Abstract, introduction, system or method, training/data, evaluations, safety or limitations, conclusion, appendices |
| Research summary | Abstract, question, method, key results, limitations, takeaways |
| Whitepaper | Abstract, problem, proposed approach, evidence, implications, limitations, conclusion |
| General report (fallback) | Overview, context, analysis, findings, implications or recommendations, limitations, conclusion |

In every mode, adapt the structure to the actual content and argument. Add, remove, rename, reorder, or merge sections as needed; never include a section merely because it appears in the table. Use the general report narrative when the requested scope does not fit one of the four specialized modes.

Do not add a cover page, executive-summary box, or table of contents by default. Enable the template's long-report contents page only when the document is roughly 20 pages or longer or the user requests one.

## 2. Build an evidence-backed outline

Read all supplied sources before drafting. When repository context matters, inspect the smallest relevant set of files. Research external facts only when the task requires it and the environment permits it.

Track separately:

- Source-supported facts, measurements, and quotations.
- Scientific publications, with enough metadata to verify and cite them correctly.
- Operational evidence such as experiment dashboards, Slack threads, issue trackers, datasets, repositories, and official webpages.
- Reproducible calculations and transformations.
- The authors' claims and contributions.
- Your synthesis or interpretation.
- Missing evidence, uncertainty, and limitations.

Maintain a source ledger with the claim supported, source type, stable URL or identifier, access date when useful, and intended citation form. Never invent citations, benchmarks, ablations, sample sizes, author names, affiliations, model details, or statistical significance. Prefer primary sources for technical claims. Attach citations or descriptive evidence links to the claims they support.

Write a one-sentence central claim and a section outline before drafting. In the introduction, state the problem, why it matters, the approach, principal results, and contributions. Keep related work comparative rather than encyclopedic.

## 3. Create the LaTeX project

Resolve the user's requested delivery location to an absolute path before starting. If none is supplied, use an absolute path under `output/latex-report/<paper-slug>/` for the final handoff.

Construct the report in a unique system temporary directory, never directly in the current working tree. Keep generated TeX, downloaded source material, figures, compiler output, and rendered QA pages inside that temporary workspace until the report passes final validation. This applies even when the requested delivery location is inside the current repository.

On macOS or Linux, create the workspace with:

```bash
FINAL_DIR="$(python3 -c 'from pathlib import Path; print(Path("output/latex-report/<paper-slug>").resolve())')"
WORK_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/latex-report.XXXXXX")"
PROJECT_DIR="$WORK_ROOT/<paper-slug>"
```

Use the temporary project for construction:

```text
<system-temp>/latex-report.XXXXXX/<paper-slug>/
├── main.tex
├── references.bib
├── figures/
├── tables/               # only when separate files improve maintainability
└── build/
```

Prefer the bundled builder because it keeps structure separate from styling and creates section files from the chosen outline. Run commands from any directory by setting `SKILL_DIR` to the directory containing this `SKILL.md`:

```bash
python3 "$SKILL_DIR/scripts/build_report.py" doctor

python3 "$SKILL_DIR/scripts/build_report.py" init "$PROJECT_DIR" \
  --title "<title>" \
  --section "<first section>" \
  --section "<second section>" \
  --section "<third section>"
```

Determine the actual outline before running `init` and pass each section with `--section`. Omit `--section` only when a narrative's suggested starting outline is genuinely appropriate; select it with `--mode research-paper`, `technical-report`, `research-summary`, `whitepaper`, or `general-report`. Use repeated `--appendix` options for appendices and `--long-report` only when a contents page materially improves navigation.

The builder creates `main.tex`, `latex-report.sty`, `references.bib`, `figures/`, and separate `sections/` files. Edit the generated section files rather than maintaining a large fixed outline in `main.tex`. Values passed to `--authors`, `--affiliations`, and `--links` may contain LaTeX; pass a plain-text `--pdf-authors` value when using formatted author markup.

Do not `cd` into or initialize the project under the repository merely for convenience. If a compiler requires the project as its working directory, run it from `PROJECT_DIR`, which is temporary. Use absolute paths for source inputs outside the temporary workspace, or copy only the required inputs into it.

If the builder cannot be used, copy both `assets/report-template.tex` and `assets/latex-report.sty` into the project, rename the template to `main.tex`, replace every `[[...]]` placeholder, and insert only the sections the document needs.

Preserve these defaults unless a venue or brand guide overrides them:

- Letter paper, single column, generous compact margins, serif body, and strong sans-serif headings.
- Left-aligned series label, title, authors, affiliations, correspondence, and artifact links, followed by a restrained abstract panel with a faint neutral fill, hairline border, and label aligned to its text inset.
- Thin rules beneath major numbered sections, centered page numbers, and no running marketing header.
- Warm-neutral body text with a muted cool accent reserved for links and small navigational details.
- Full-width figures and tables with restrained captions, sparse rules, and ample surrounding whitespace.
- Author-year citations using `natbib` or the bibliography system already required by the project.

## 4. Write and typeset like an ML paper

Use precise prose, compact paragraphs, and informative headings. Define notation before use. State experimental setup well enough to assess or reproduce the work: data, splits, baselines, hyperparameters, evaluation protocols, compute, and uncertainty when available.

For results:

- Put the takeaway in the surrounding prose and the measurements in the figure or table.
- Use vector PDF plots when possible and high-resolution raster images otherwise.
- Use `booktabs` tables with no vertical rules. Align decimal values and label units.
- Bold the best result only when comparisons are valid; use underlining for second-best sparingly.
- Report sample sizes, variation, error bars, or confidence intervals when the source supports them.
- Give every figure and table a self-contained caption, label, and explicit reference in the text.
- Use full-width figures for central model diagrams or benchmark summaries; avoid decorative graphics.
- Design figures for their final printed size. Axis labels, legends, and annotations must remain comfortably readable at 100% PDF zoom; treat roughly 8-point text as a practical minimum.
- Split or crop dense multi-panel composites instead of shrinking an entire dashboard into the text width. A six-panel plot usually needs separate figures, selected panels, or a dedicated landscape/full-page treatment.
- When source charts remain illegible after cropping, redraw the supported measurements as a clean vector plot with larger typography and simpler encoding. Preserve the values, disclose that the figure was replotted or adapted, and do not imply precision absent from the source.
- Inspect cropped panels at their edges. Reject crops that retain slivers of adjacent panels, clipped labels, duplicate titles, or excess blank canvas.
- Keep each figure or table with the subsection that interprets it. Finish the preceding paragraph, place the float, then add `\ReportFloatBarrier` before moving to the next analytical subsection when several floats could queue.
- Never allow a float-only page to interrupt a sentence or separate a result from its explanation. Reorder text, reduce float size, crop panels, or add a barrier rather than accepting that layout.
- Keep page one focused on front matter, abstract, and the opening argument. Move dense result tables off the first page unless they are the document's central executive artifact.

Use footnotes for genuinely secondary details. Move extensive ablations, prompts, dataset examples, evaluation details, and additional tables to appendices rather than compressing the main argument.

## 5. Handle citations and research integrity

Create `references.bib` whenever the report cites scientific literature, and use it for citation-heavy reports. Every scientific work that is clearly identifiable and materially supports the report must have a verified bibliographic entry and an in-text citation. Prefer DOI, arXiv, ACL Anthology, publisher, or official project metadata. Preserve the user's requested citation style when supplied. Do not add speculative related work merely to populate a bibliography.

Treat non-scholarly evidence as citable source material:

- Link to the most specific stable source available: a Slack message permalink rather than a channel, a particular dashboard or run comparison rather than a portal homepage, and a specific issue, commit, dataset version, or webpage rather than a generic site.
- Use descriptive link text that names the artifact and, when useful, its owner and date. Never make a raw URL carry the explanatory burden.
- Cite material evidence close to the supported claim and include a compact ``Sources and Evidence'' or provenance subsection when several operational sources are used.
- Mark internal or access-restricted links as such; retain a human-readable artifact name or identifier so the reference remains useful without access.
- Put source attribution in every reproduced or adapted figure and table caption, with a clickable link when the source has one.
- If no external scientific publication is clearly identified, say so when that absence matters; do not infer a paper from a vague name or internal shorthand.

Before compiling, verify:

- Every citation resolves to a real entry and supports the nearby claim.
- Every bibliography entry is cited unless the user requests a reading list.
- Names, title, venue, year, URL, DOI, and arXiv identifier match the source.
- Every material Slack thread, dashboard, repository, dataset, issue, and webpage has a working descriptive hyperlink or stable identifier.
- Links point to the specific supporting artifact rather than a generic landing page whenever possible.
- Direct quotations are exact, short, and clearly attributed.
- Tables and figures identify whether values are reproduced, adapted, or newly calculated.

Never disguise a generated interpretation as an experimental result. Mark missing experiments and unresolved evidence explicitly.

## 6. Compile and repair

Use the builder for deterministic compiler detection, compilation, rendering, and static QA:

```bash
python3 "$SKILL_DIR/scripts/build_report.py" build \
  "$PROJECT_DIR/main.tex"
```

The script checks `PATH`, standard MacTeX paths on macOS, standard TeX Live paths on Linux, and bundled Tectonic locations. It prefers `latexmk`, falls back to Tectonic or a direct engine, never installs software, and reports missing tools. Use `--engine xelatex` or `--engine lualatex` for substantial Unicode or custom-font needs. Use `--allow-placeholders` only for template smoke tests, never for final delivery.

If the builder cannot be used, prefer:

```bash
(cd "$PROJECT_DIR" && latexmk -pdf -interaction=nonstopmode \
  -halt-on-error -outdir=build main.tex)
(cd "$PROJECT_DIR" && tectonic main.tex --outdir build)
(cd "$PROJECT_DIR" && latexmk -xelatex -interaction=nonstopmode \
  -halt-on-error -outdir=build main.tex)
```

Use `latexmk` for bibliographies and cross-references when available. Do not install a TeX distribution without approval.

Read the complete compiler log. Fix errors and meaningful warnings, including unresolved citations or references, missing glyphs, duplicate labels, float problems, and visible overfull boxes. Recompile until references, bibliography, and page count stabilize.

## 7. Render and inspect every page

The builder renders with Poppler when `pdftoppm` is available and writes page images under `build/rendered/`. If rendering is unavailable, report the missing tool rather than silently skipping visual QA. For manual rendering:

```bash
mkdir -p "$WORK_ROOT/rendered-paper"
pdftoppm -png -r 150 "$PROJECT_DIR/build/main.pdf" \
  "$WORK_ROOT/rendered-paper/page"
```

Inspect every page. Check:

- Title, authors, affiliations, abstract, and artifact links fit naturally on page one.
- The abstract label aligns cleanly with the abstract text, and its panel remains subtle enough not to compete with the title or first numbered section.
- No clipped, overlapping, missing, or microscopic text.
- No orphaned headings, awkward widows, sparse accidental pages, or broken floats.
- Equations, algorithms, figures, and tables are legible at normal zoom.
- No chart depends on zooming to read panel titles, axis labels, legends, or data annotations.
- Raster screenshots and cropped source plots have clean boundaries with no neighboring-panel remnants; adapted plots preserve the source values and say that they were replotted.
- No float-only page appears between two halves of a paragraph, and no sentence resumes after one or more pages of figures.
- Figures and tables appear in the same local reading context as their first interpretation; add `\ReportFloatBarrier` where needed.
- Section rules are visually separated from heading text and do not resemble underlines.
- Page density is balanced: avoid overpacked first pages, isolated headings, and nearly empty trailing pages when a small reflow would improve continuity.
- Captions, numbering, references, footnotes, bibliography, and appendices are consistent.
- Scientific citations are complete, operational evidence links are clickable, and restricted sources remain intelligible from their labels.
- The paper remains understandable in grayscale and uses color accessibly.
- No `[[...]]`, TODO, dummy citation, sample result, or instructional text remains.

Revise, compile, and render again after every material layout change. Do not deliver a PDF with a known defect.

## 8. Deliver the project

After the temporary project passes compilation and full-page visual QA, create `FINAL_DIR` and publish only the editable source set and the descriptively named final PDF. Exclude `build/`, rendered page images, compiler auxiliaries, downloaded reference copies, caches, and unused assets. Verify the published PDF opens and matches the validated temporary PDF before removing the temporary workspace.

Remove `WORK_ROOT` after successful publication. If publication or validation fails, retain the temporary workspace for diagnosis and report its absolute path rather than copying a partial project into the delivery location.

Return the editable LaTeX project and compiled PDF with absolute paths or host-supported links. Summarize the central claim, sources used, assumptions, and unresolved evidence. Include the primary compile command against the delivered project so the result is reproducible.

Do not include rendered page images, auxiliary compiler files, downloaded references, or unused assets in the final handoff.
