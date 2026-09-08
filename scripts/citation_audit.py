#!/usr/bin/env python3
"""Mechanical bibliography/citation consistency audit for paper sources."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

TEXT_EXTS = {".md", ".tex", ".txt"}
BIB_KEY_RE = re.compile(r"@\w+\s*\{\s*([^,\s]+)\s*,", re.I)
LATEX_CITE_RE = re.compile(r"\\cite\w*\{([^}]+)\}")
PANDOC_CITE_RE = re.compile(r"\[@([^\]]+)\]")
NUMERIC_CITE_RE = re.compile(r"\[(\d+(?:\s*[,–-]\s*\d+)*)\]")
REF_HEADING_RE = re.compile(r"^\s*(?:#+\s*)?(参考文献|References|Bibliography)\s*$", re.I | re.M)
REF_ENTRY_RE = re.compile(r"^\s*(?:\[(\d+)\]|(\d+)[.、])\s+\S+", re.M)


def read_paper(path: Path):
    if path.is_file():
        return path.read_text(encoding="utf-8", errors="replace"), [str(path)]
    files = sorted(p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in TEXT_EXTS)
    return "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in files), [str(p) for p in files]


def split_body_refs(text: str):
    matches = list(REF_HEADING_RE.finditer(text))
    if not matches:
        return text, ""
    m = matches[-1]
    return text[:m.start()], text[m.end():]


def keyed_citations(text: str):
    keys = set()
    for m in LATEX_CITE_RE.finditer(text):
        keys.update(k.strip() for k in m.group(1).split(",") if k.strip())
    for m in PANDOC_CITE_RE.finditer(text):
        for token in re.findall(r"@([A-Za-z0-9_:.+\-/]+)", "@" + m.group(1)):
            keys.add(token)
    return keys


def bib_keys(path: Path):
    return set(BIB_KEY_RE.findall(path.read_text(encoding="utf-8", errors="replace")))


def audit(paper: Path, bibliography: Path | None = None, strict_unused=False):
    text, files = read_paper(paper)
    body, refs = split_body_refs(text)
    issues = []
    cited_keys = keyed_citations(body)

    if bibliography is None and paper.is_dir():
        bibs = sorted(paper.rglob("*.bib"))
        bibliography = bibs[0] if len(bibs) == 1 else None

    result = {"paper": str(paper), "files": files, "bibliography": str(bibliography) if bibliography else None}
    if bibliography:
        defined = bib_keys(bibliography)
        undefined = sorted(cited_keys - defined)
        unused = sorted(defined - cited_keys)
        if defined and not cited_keys:
            issues.append({"severity": "error", "code": "zero-body-citations",
                           "detail": f"Bibliography defines {len(defined)} entries but the paper body cites none"})
        if undefined:
            issues.append({"severity": "error", "code": "undefined-citations", "keys": undefined})
        if unused:
            issues.append({"severity": "error" if strict_unused else "review", "code": "uncited-bibliography", "keys": unused})
        result.update(mode="keyed", defined=sorted(defined), cited=sorted(cited_keys),
                      undefined=undefined, uncited=unused)
    else:
        ref_entries = sorted({int(a or b) for a, b in REF_ENTRY_RE.findall(refs)}) if refs else []
        numeric = sorted({m.group(1) for m in NUMERIC_CITE_RE.finditer(body)})
        if ref_entries and not numeric and not cited_keys:
            issues.append({"severity": "error", "code": "zero-body-citations",
                           "detail": f"Reference section contains {len(ref_entries)} numbered entries but the paper body cites none"})
        if not ref_entries and not cited_keys:
            issues.append({"severity": "review", "code": "no-reference-structure",
                           "detail": "No .bib file or numbered reference section was detected; citation consistency could not be fully checked"})
        result.update(mode="numeric", reference_entries=ref_entries,
                      numeric_citation_tokens=numeric, keyed_citations=sorted(cited_keys))

    if any(i["severity"] == "error" for i in issues):
        status = "failed"
    elif issues:
        status = "needs_review"
    else:
        status = "passed"
    result.update(issues=issues, status=status)
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paper", type=Path, required=True, help="Paper source file or directory")
    ap.add_argument("--bibliography", type=Path, help="Optional BibTeX file; auto-detected when exactly one .bib exists")
    ap.add_argument("--strict-unused", action="store_true", help="Treat uncited bibliography entries as errors")
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    report = audit(a.paper, a.bibliography, a.strict_unused)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "issues": len(report["issues"]), "output": str(a.output)}))
    raise SystemExit(1 if report["status"] == "failed" else 0)


if __name__ == "__main__":
    main()
