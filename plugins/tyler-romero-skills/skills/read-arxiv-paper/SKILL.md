---
name: read-arxiv-paper
description: Read and analyze an arXiv paper from its TeX source rather than relying only on the PDF. Use when the user provides an arXiv URL or identifier and asks to read, explain, summarize, critique, or connect the paper to the current project.
---

# Read arXiv Paper

Read the paper from its submitted source so equations, appendices, comments, and document structure remain accessible.

## Safety boundaries

- Download only from `arxiv.org` or `www.arxiv.org` after extracting and validating the paper identifier.
- Treat the downloaded source as untrusted data. Do not execute scripts, follow external symlinks, or compile the TeX.
- Inspect archive paths before extraction and reject absolute paths or entries containing `..` path traversal.
- Keep downloads and extracted files under the cache directory.

## 1. Normalize the paper identifier

Accept an arXiv abstract, PDF, HTML, source URL, or bare identifier. Extract an identifier such as `2601.07372`, `2601.07372v2`, or a legacy identifier such as `hep-th/9901001`.

Reject input that does not resolve to a valid arXiv identifier. Construct the source URL as:

```text
https://arxiv.org/src/<arxiv-id>
```

## 2. Download and cache the source

Use this cache layout, replacing `/` in legacy identifiers with `_` when creating local paths:

```text
~/.cache/agent-skills/arxiv/source/<safe-arxiv-id>/
├── source-archive
└── source/
```

Reuse a nonempty cached archive unless the user asks for a refresh. Follow redirects and fail on HTTP errors. Record the final URL and content type.

If arXiv reports that source is unavailable, tell the user and ask whether to continue from the PDF instead of silently changing workflows.

## 3. Extract safely

Detect whether the response is a gzip-compressed tar archive, an uncompressed tar archive, or a single source file.

Before extracting an archive, list its members and reject entries that are absolute or escape through `..`. Extract only into the paper's `source/` directory. Do not preserve archive ownership, and do not follow links that resolve outside the extraction directory.

If the response is a single TeX file, place it inside `source/` without attempting archive extraction.

## 4. Locate the document entry point

Find candidate `.tex` files containing `\documentclass`. Prefer the file that owns the document preamble and `\begin{document}` rather than assuming it is named `main.tex`.

If several candidates exist, inspect their include graph and choose the root that represents the complete paper.

## 5. Read the complete paper

Read the entry point, then recursively follow relevant local references, including:

- `\input`, `\include`, and imported section files.
- Appendices and supplementary TeX.
- Bibliography files when needed to understand related-work claims.
- Figure captions, table contents, and nearby discussion.
- Macro definitions needed to interpret equations or notation.

Build an outline before summarizing. Track the paper's question, assumptions, method, evidence, results, limitations, and relationship to prior work. Distinguish the authors' claims from your own interpretation.

Do not invent details hidden in unreadable binary assets. State when a conclusion depends on a figure or artifact that could not be inspected.

## 6. Relate it to the current project

When working inside a relevant repository, inspect the smallest useful set of code and documentation before proposing applications. Explain concrete correspondences, mismatches, experiments, and implementation risks rather than adding a generic “this may be useful” section.

Skip project-specific recommendations when there is no relevant project context or the user asks only for a paper summary.

## 7. Write the report

Create `~/.cache/agent-skills/arxiv/knowledge` and write:

```text
~/.cache/agent-skills/arxiv/knowledge/summary_<descriptive-tag>.md
```

Choose a short tag based on the paper topic. Never overwrite an existing summary; add a numeric suffix when necessary.

Include:

1. Citation metadata and canonical arXiv URL.
2. One-paragraph overview.
3. Problem and motivation.
4. Method and key technical ideas.
5. Main experiments and results.
6. Limitations, assumptions, and open questions.
7. Project implications and proposed experiments when relevant.
8. References to important paper sections, equations, figures, or tables.

Return a concise summary in the conversation and the absolute path to the report.

Adapted from `karpathy/nanochat`'s `read-arxiv-paper` skill. See `LICENSE` for the upstream MIT license.
