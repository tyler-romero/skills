#!/usr/bin/env python3
"""Scaffold, compile, render, and validate adaptable LaTeX reports."""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import platform
import re
import shutil
import subprocess
from pathlib import Path
from typing import Iterable


SKILL_DIR = Path(__file__).resolve().parents[1]
ASSETS_DIR = SKILL_DIR / "assets"
TEMPLATE_PATH = ASSETS_DIR / "report-template.tex"
STYLE_PATH = ASSETS_DIR / "latex-report.sty"

MODE_OUTLINES = {
    "research-paper": [
        "Introduction",
        "Related Work",
        "Method",
        "Experimental Setup",
        "Results and Analysis",
        "Limitations",
        "Conclusion",
    ],
    "technical-report": [
        "Introduction",
        "System or Method",
        "Data and Training",
        "Evaluation",
        "Limitations and Safety",
        "Conclusion",
    ],
    "research-summary": [
        "Research Question",
        "Method",
        "Key Results",
        "Limitations",
        "Takeaways",
    ],
    "whitepaper": [
        "Problem",
        "Proposed Approach",
        "Evidence",
        "Implications",
        "Limitations",
        "Conclusion",
    ],
    "general-report": [
        "Overview",
        "Context",
        "Analysis",
        "Findings",
        "Implications",
        "Limitations",
        "Conclusion",
    ],
}

TOOL_NAMES = (
    "latexmk",
    "pdflatex",
    "xelatex",
    "lualatex",
    "tectonic",
    "bibtex",
    "biber",
    "pdftoppm",
    "pdfinfo",
)

HARD_LOG_PATTERNS = {
    "undefined references": re.compile(r"undefined references", re.IGNORECASE),
    "undefined citations": re.compile(r"undefined citations", re.IGNORECASE),
    "missing character": re.compile(r"Missing character", re.IGNORECASE),
    "overfull box": re.compile(r"Overfull \\[hv]box"),
    "latex error": re.compile(r"! LaTeX Error:"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scaffold, build, render, and validate a LaTeX report project."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser(
        "doctor", help="Detect available LaTeX and PDF tools."
    )
    doctor.add_argument(
        "--json", action="store_true", help="Emit machine-readable output."
    )

    init = subparsers.add_parser(
        "init", help="Create an outline-driven report project."
    )
    init.add_argument("output_dir", type=Path)
    init.add_argument("--title", default="Untitled Report")
    init.add_argument("--series", default="")
    init.add_argument("--authors", default="")
    init.add_argument("--pdf-authors", default="")
    init.add_argument("--affiliations", default="")
    init.add_argument("--correspondence", default="")
    init.add_argument("--date", default=dt.date.today().strftime("%B %Y"))
    init.add_argument("--links", default="")
    init.add_argument("--keywords", default="")
    init.add_argument(
        "--abstract",
        default="[[Write a self-contained abstract for this document.]]",
    )
    init.add_argument("--mode", choices=sorted(MODE_OUTLINES), default="general-report")
    init.add_argument(
        "--section",
        action="append",
        default=[],
        help="Section title. Repeat to supply the actual outline; overrides --mode.",
    )
    init.add_argument(
        "--appendix",
        action="append",
        default=[],
        help="Appendix title. Repeat for multiple appendices.",
    )
    init.add_argument("--long-report", action="store_true")
    init.add_argument("--json", action="store_true")

    build = subparsers.add_parser(
        "build", help="Compile, render, and validate a report."
    )
    build.add_argument("main_tex", type=Path)
    build.add_argument("--output-directory", type=Path)
    build.add_argument(
        "--engine",
        choices=("auto", "pdflatex", "xelatex", "lualatex", "tectonic"),
        default="auto",
    )
    build.add_argument("--no-render", action="store_true")
    build.add_argument("--render-dpi", type=int, default=150)
    build.add_argument("--allow-placeholders", action="store_true")
    build.add_argument("--json", action="store_true")

    return parser.parse_args()


def extra_tool_directories(system: str | None = None) -> list[Path]:
    system = system or platform.system()
    directories: list[Path] = []
    if system == "Darwin":
        directories.append(Path("/Library/TeX/texbin"))
        directories.extend(
            Path(path)
            for path in glob.glob("/usr/local/texlive/*/bin/universal-darwin")
        )
    elif system == "Linux":
        directories.extend(
            Path(path) for path in glob.glob("/usr/local/texlive/*/bin/*-linux")
        )

    directories.extend(
        Path(path)
        for path in glob.glob(
            str(Path.home() / ".codex/plugins/cache/openai-bundled/latex/*/bin")
        )
    )
    return directories


def find_tool(
    name: str, system: str | None = None, search_path: str | None = None
) -> str | None:
    if path := shutil.which(name, path=search_path):
        return path
    for directory in extra_tool_directories(system):
        candidate = directory / name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def detect_tools(
    system: str | None = None, search_path: str | None = None
) -> dict[str, str | None]:
    return {name: find_tool(name, system, search_path) for name in TOOL_NAMES}


def doctor_result() -> dict[str, object]:
    tools = detect_tools()
    ready = any(tools[name] for name in ("tectonic", "pdflatex", "xelatex", "lualatex"))
    return {
        "platform": platform.system(),
        "ready": ready,
        "tools": tools,
        "note": "No tools are installed or modified by this script.",
    }


def latex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(character, character) for character in value)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "section"


def ensure_new_directory(path: Path) -> Path:
    path = path.expanduser().resolve()
    if path.exists() and not path.is_dir():
        raise SystemExit(f"Output path exists but is not a directory: {path}")
    if path.exists() and any(path.iterdir()):
        raise SystemExit(f"Refusing to overwrite nonempty directory: {path}")
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_section_files(directory: Path, titles: Iterable[str]) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    used_names: set[str] = set()
    for index, title in enumerate(titles, start=1):
        base = f"{index:02d}-{slugify(title)}"
        name = base
        suffix = 2
        while name in used_names:
            name = f"{base}-{suffix}"
            suffix += 1
        used_names.add(name)
        path = directory / f"{name}.tex"
        content = (
            f"\\section{{{latex_escape(title)}}}\n\n"
            "[[Develop this section from the document's actual evidence and argument.]]\n"
        )
        path.write_text(content, encoding="utf-8")
        paths.append(path)
    return paths


def input_lines(paths: Iterable[Path], project: Path) -> str:
    return "\n\n".join(
        rf"\input{{{path.relative_to(project).with_suffix('').as_posix()}}}"
        for path in paths
    )


def scaffold(args: argparse.Namespace) -> dict[str, object]:
    project = ensure_new_directory(args.output_dir)
    sections = args.section or MODE_OUTLINES[args.mode]
    section_paths = write_section_files(project / "sections", sections)
    appendix_paths = write_section_files(project / "appendices", args.appendix)

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    replacements = {
        "[[REPORT_SERIES]]": latex_escape(args.series),
        "[[REPORT_TITLE]]": latex_escape(args.title),
        "[[REPORT_AUTHORS]]": args.authors,
        "[[REPORT_PDF_AUTHORS]]": latex_escape(args.pdf_authors or args.authors),
        "[[REPORT_AFFILIATIONS]]": args.affiliations,
        "[[REPORT_CORRESPONDENCE]]": args.correspondence,
        "[[REPORT_DATE]]": latex_escape(args.date),
        "[[REPORT_LINKS]]": args.links,
        "[[REPORT_KEYWORDS]]": latex_escape(args.keywords),
        "[[LONG_REPORT_SETTING]]": r"\longreporttrue"
        if args.long_report
        else r"\longreportfalse",
        "[[ABSTRACT]]": args.abstract,
        "% [[SECTIONS]]": input_lines(section_paths, project),
        "% [[APPENDICES]]": (
            "\\appendix\n\n" + input_lines(appendix_paths, project)
            if appendix_paths
            else ""
        ),
    }
    for marker, value in replacements.items():
        template = template.replace(marker, value)

    main_tex = project / "main.tex"
    main_tex.write_text(template, encoding="utf-8")
    shutil.copy2(STYLE_PATH, project / STYLE_PATH.name)
    (project / "references.bib").touch()
    (project / "figures").mkdir()

    return {
        "project": str(project),
        "mainTex": str(main_tex),
        "style": str(project / STYLE_PATH.name),
        "sections": [str(path) for path in section_paths],
        "appendices": [str(path) for path in appendix_paths],
        "mode": args.mode,
        "usedExplicitOutline": bool(args.section),
    }


def run_command(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def select_engine(
    requested: str, tools: dict[str, str | None]
) -> tuple[str, str, bool]:
    if requested == "tectonic":
        if not tools["tectonic"]:
            raise SystemExit("Tectonic was requested but was not found.")
        return "tectonic", tools["tectonic"], False

    engine = "pdflatex" if requested == "auto" else requested
    if tools["latexmk"] and tools[engine]:
        return engine, tools["latexmk"], True
    if requested == "auto" and tools["tectonic"]:
        return "tectonic", tools["tectonic"], False
    if tools[engine]:
        return engine, tools[engine], False
    raise SystemExit(
        "No usable LaTeX compiler found. Run the doctor command and install TeX Live, "
        "MacTeX, or Tectonic outside this script."
    )


def compile_report(
    main_tex: Path,
    output_dir: Path,
    requested_engine: str,
    tools: dict[str, str | None],
) -> dict[str, object]:
    engine, executable, uses_latexmk = select_engine(requested_engine, tools)
    main_tex = main_tex.resolve()
    project = main_tex.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    if uses_latexmk:
        engine_flag = {
            "pdflatex": "-pdf",
            "xelatex": "-xelatex",
            "lualatex": "-lualatex",
        }[engine]
        command = [
            executable,
            "-norc",
            engine_flag,
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-file-line-error",
            f"-outdir={output_dir}",
            main_tex.name,
        ]
        result = run_command(command, project)
        commands = [command]
        log = result.stdout
        return_code = result.returncode
    elif engine == "tectonic":
        command = [
            executable,
            "-X",
            "compile",
            "--outdir",
            str(output_dir),
            "--outfmt",
            "pdf",
            "--keep-logs",
            "--print",
            "--untrusted",
            main_tex.name,
        ]
        result = run_command(command, project)
        commands = [command]
        log = result.stdout
        return_code = result.returncode
    else:
        command = [
            executable,
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-file-line-error",
            f"-output-directory={output_dir}",
            main_tex.name,
        ]
        commands = []
        logs = []
        result = run_command(command, project)
        commands.append(command)
        logs.append(result.stdout)
        return_code = result.returncode

        bibliography_ran = False
        if return_code == 0:
            bcf = output_dir / f"{main_tex.stem}.bcf"
            aux = output_dir / f"{main_tex.stem}.aux"
            bibliography_command: list[str] | None = None
            bibliography_target = output_dir / main_tex.stem
            try:
                bibliography_argument = bibliography_target.relative_to(project)
            except ValueError:
                bibliography_argument = bibliography_target
            if bcf.is_file():
                if tools["biber"]:
                    bibliography_command = [tools["biber"], str(bibliography_argument)]
                else:
                    logs.append("Biber input detected, but biber was not found.")
                    return_code = 1
            elif aux.is_file() and "\\bibdata" in aux.read_text(
                encoding="utf-8", errors="ignore"
            ):
                if tools["bibtex"]:
                    bibliography_command = [tools["bibtex"], str(bibliography_argument)]
                else:
                    logs.append("BibTeX input detected, but bibtex was not found.")
                    return_code = 1

            if bibliography_command:
                bibliography_result = run_command(bibliography_command, project)
                commands.append(bibliography_command)
                logs.append(bibliography_result.stdout)
                return_code = bibliography_result.returncode
                bibliography_ran = return_code == 0

        if return_code == 0:
            passes = 2 if bibliography_ran else 1
            for _ in range(passes):
                result = run_command(command, project)
                commands.append(command)
                logs.append(result.stdout)
                return_code = result.returncode
                if return_code:
                    break
        log = "\n".join(logs)

    pdf = output_dir / f"{main_tex.stem}.pdf"
    log_path = output_dir / f"{main_tex.stem}.log"
    final_log = (
        log_path.read_text(encoding="utf-8", errors="ignore")
        if log_path.is_file()
        else log
    )
    return {
        "engine": engine,
        "usesLatexmk": uses_latexmk,
        "commands": commands,
        "exitCode": return_code,
        "output": log,
        "log": final_log,
        "pdf": str(pdf),
        "pdfExists": pdf.is_file(),
    }


def source_files(project: Path, output_dir: Path) -> list[Path]:
    files = []
    for pattern in ("*.tex", "*.bib"):
        for path in project.rglob(pattern):
            if output_dir not in path.parents:
                files.append(path)
    return sorted(files)


def inspect_sources(project: Path, output_dir: Path) -> dict[str, list[str]]:
    placeholders: list[str] = []
    todos: list[str] = []
    layout_warnings: list[str] = []
    source_warnings: list[str] = []
    placeholder_pattern = re.compile(r"\[\[[^\n]*?\]\]")
    todo_pattern = re.compile(r"\b(?:TODO|FIXME)\b")
    files = source_files(project, output_dir)
    combined_text = ""
    for path in files:
        text = path.read_text(encoding="utf-8")
        combined_text += "\n" + text
        for line_number, line in enumerate(text.splitlines(), start=1):
            if placeholder_pattern.search(line):
                placeholders.append(f"{path}:{line_number}: {line.strip()}")
            if todo_pattern.search(line):
                todos.append(f"{path}:{line_number}: {line.strip()}")
        float_count = len(re.findall(r"\\begin\{(?:figure|table)\}", text))
        if (
            path.suffix == ".tex"
            and float_count >= 2
            and "\\ReportFloatBarrier" not in text
        ):
            layout_warnings.append(
                f"{path}: contains {float_count} floats without a ReportFloatBarrier"
            )
        if path.suffix == ".tex":
            figure_blocks = re.findall(
                r"\\begin\{figure\}.*?\\end\{figure\}", text, re.DOTALL
            )
            for figure_index, block in enumerate(figure_blocks, start=1):
                image_count = len(re.findall(r"\\includegraphics", block))
                if image_count >= 2:
                    layout_warnings.append(
                        f"{path}: figure {figure_index} contains {image_count} images; "
                        "verify every panel and label is readable at 100% zoom"
                    )
    bib_entry_count = sum(
        len(re.findall(r"(?m)^\s*@\w+\s*\{", path.read_text(encoding="utf-8")))
        for path in files
        if path.suffix == ".bib"
    )
    has_bibliography = bool(
        re.search(
            r"\\(?:bibliography|addbibresource|printbibliography)\b", combined_text
        )
    )
    citation_count = len(re.findall(r"\\cite\w*\s*(?:\[[^]]*\]\s*)*\{", combined_text))
    hyperlink_count = len(re.findall(r"\\(?:href|url)\s*\{", combined_text))
    if bib_entry_count and not has_bibliography:
        source_warnings.append(
            f"references.bib contains {bib_entry_count} entries but no bibliography is rendered"
        )
    if citation_count == 0 and hyperlink_count == 0:
        source_warnings.append(
            "no citations or hyperlinks detected; confirm the report does not rely on external sources"
        )
    return {
        "placeholders": placeholders,
        "todos": todos,
        "layoutWarnings": layout_warnings,
        "sourceWarnings": source_warnings,
    }


def inspect_log(log: str) -> list[str]:
    return [
        label for label, pattern in HARD_LOG_PATTERNS.items() if pattern.search(log)
    ]


def render_pdf(
    pdf: Path, output_dir: Path, dpi: int, tool: str | None
) -> dict[str, object]:
    if not tool:
        return {
            "status": "unavailable",
            "reason": "pdftoppm was not found",
            "pages": [],
        }
    rendered_dir = output_dir / "rendered"
    if rendered_dir.exists():
        shutil.rmtree(rendered_dir)
    rendered_dir.mkdir(parents=True)
    prefix = rendered_dir / "page"
    command = [tool, "-png", "-r", str(dpi), str(pdf), str(prefix)]
    result = run_command(command, pdf.parent)
    pages = sorted(rendered_dir.glob("page-*.png"))
    return {
        "status": "rendered" if result.returncode == 0 else "failed",
        "command": command,
        "exitCode": result.returncode,
        "output": result.stdout,
        "pages": [str(path) for path in pages],
    }


def build(args: argparse.Namespace) -> dict[str, object]:
    main_tex = args.main_tex.expanduser().resolve()
    if not main_tex.is_file():
        raise SystemExit(f"Main TeX file not found: {main_tex}")
    output_dir = (
        args.output_directory.expanduser().resolve()
        if args.output_directory
        else main_tex.parent / "build"
    )
    tools = detect_tools()
    compilation = compile_report(main_tex, output_dir, args.engine, tools)
    sources = inspect_sources(main_tex.parent, output_dir)
    log_issues = inspect_log(str(compilation["log"]))
    pdf = Path(str(compilation["pdf"]))
    rendering = (
        {"status": "skipped", "pages": []}
        if args.no_render or not compilation["pdfExists"]
        else render_pdf(pdf, output_dir, args.render_dpi, tools["pdftoppm"])
    )
    blockers = []
    if compilation["exitCode"] != 0 or not compilation["pdfExists"]:
        blockers.append("compilation failed")
    blockers.extend(log_issues)
    if sources["placeholders"] and not args.allow_placeholders:
        blockers.append("unresolved placeholders")
    if not args.no_render and rendering["status"] != "rendered":
        blockers.append(f"rendering {rendering['status']}")
    return {
        "ok": not blockers,
        "platform": platform.system(),
        "mainTex": str(main_tex),
        "outputDirectory": str(output_dir),
        "tools": tools,
        "compilation": compilation,
        "rendering": rendering,
        "qa": {
            **sources,
            "logIssues": log_issues,
            "blockers": blockers,
        },
    }


def emit(result: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2))
        return
    if "ready" in result:
        print(f"Platform: {result['platform']}")
        print(f"Ready: {'yes' if result['ready'] else 'no'}")
        for name, path in result["tools"].items():
            print(f"{name}: {path or 'not found'}")
        print(result["note"])
        return
    if "project" in result:
        print(f"Project created: {result['project']}")
        print(f"Main file: {result['mainTex']}")
        print(f"Sections: {len(result['sections'])}")
        print(f"Appendices: {len(result['appendices'])}")
        return
    print(f"Build: {'passed' if result['ok'] else 'failed'}")
    print(f"PDF: {result['compilation']['pdf']}")
    print(f"Rendered pages: {len(result['rendering'].get('pages', []))}")
    blockers = result["qa"]["blockers"]
    if blockers:
        print("Blockers: " + ", ".join(blockers))
    layout_warnings = result["qa"].get("layoutWarnings", [])
    if layout_warnings:
        print("Layout warnings:")
        for warning in layout_warnings:
            print(f"- {warning}")
    source_warnings = result["qa"].get("sourceWarnings", [])
    if source_warnings:
        print("Source warnings:")
        for warning in source_warnings:
            print(f"- {warning}")


def main() -> int:
    args = parse_args()
    if args.command == "doctor":
        result = doctor_result()
    elif args.command == "init":
        result = scaffold(args)
    else:
        result = build(args)
    emit(result, args.json)
    if args.command == "doctor":
        return 0 if result["ready"] else 1
    if args.command == "build":
        return 0 if result["ok"] else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
