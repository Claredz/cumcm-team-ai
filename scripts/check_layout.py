#!/usr/bin/env python3
"""Advisory layout lint for mathematical-modeling papers.

This tool complements pdf_audit.py. It checks figure/table placement and common
layout heuristics, but does not turn inherited contest advice into official
rules. By default only deterministic corruption and an explicitly requested
hard page limit fail the command.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

CAP_RE = re.compile(r"^\s*(图|表)\s*(\d+)\s*[:：.、]?\s*(.*)$", re.S)
REF_RE = re.compile(r"(图|表)\s*(\d+)")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:[.,][0-9]+)*")
GARBLE_RE = re.compile(r"[\ufffd\u25a1\u25a0]")


def count_zi(text: str) -> int:
    text = re.sub(r"\\[A-Za-z]+\s*", " ", text)
    text = re.sub(r"[{}$~^_\\&%#]", " ", text)
    return len(CJK_RE.findall(text)) + len(TOKEN_RE.findall(text))


def extract_tex_captions(path: Path | None) -> list[dict]:
    if not path or not path.is_file():
        return []
    src = path.read_text(encoding="utf-8", errors="replace")
    out: list[dict] = []
    for match in re.finditer(r"\\caption\s*(?:\[[^\]]*\])?\s*\{", src):
        i, depth, buf = match.end(), 1, []
        while i < len(src) and depth:
            char = src[i]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
            if depth:
                buf.append(char)
            i += 1
        text = "".join(buf).strip()
        out.append({
            "line": src.count("\n", 0, match.start()) + 1,
            "text": text,
            "length": count_zi(text),
        })
    return out


def classify_caption_length(length: int, minimum: int = 100, maximum: int = 150) -> dict | None:
    if minimum <= length <= maximum:
        return None
    return {
        "severity": "hint",
        "code": "caption-length",
        "detail": f"caption length {length} is outside the inherited {minimum}-{maximum} character heuristic; review for clarity, not rule compliance",
    }


def merge_intervals(items: list[tuple[float, float]], gap: float = 12.0) -> list[tuple[float, float]]:
    if not items:
        return []
    items = sorted(items)
    merged = [list(items[0])]
    for start, end in items[1:]:
        if start <= merged[-1][1] + gap:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [(float(a), float(b)) for a, b in merged]


def _page_paragraphs(page) -> list[tuple[float, float, str, int]]:
    blocks = []
    for raw in page.get_text("blocks"):
        text = (raw[4] or "").strip()
        if text:
            blocks.append((float(raw[1]), float(raw[3]), text, count_zi(text)))
    return sorted(blocks, key=lambda item: item[0])


def _graphics_bands(page) -> list[tuple[float, float]]:
    rects: list[tuple[float, float]] = []
    width, height = float(page.rect.width), float(page.rect.height)
    try:
        for info in page.get_image_info():
            x0, y0, x1, y1 = info["bbox"]
            if (x1 - x0) * (y1 - y0) > 4:
                rects.append((float(y0), float(y1)))
    except Exception:
        pass
    try:
        drawings = page.get_drawings()
    except Exception:
        drawings = []
    for drawing in drawings:
        rect = drawing.get("rect")
        if rect is None:
            continue
        w, h = float(rect.width), float(rect.height)
        if rect.is_empty or rect.is_infinite:
            continue
        if w > 0.95 * width and h > 0.95 * height:
            continue
        if w * h < 4:
            continue
        rects.append((float(rect.y0), float(rect.y1)))
    return merge_intervals(rects)


def _detect_body_end(doc) -> int:
    for pno in range(len(doc)):
        for line in doc[pno].get_text("text").splitlines():
            text = line.strip()
            if re.match(r"^附\s*录", text) and len(text) < 30:
                return pno  # number of pages before appendix, already 1-based count
    return len(doc)


def _status(issues: list[dict]) -> str:
    if any(item["severity"] == "error" for item in issues):
        return "failed"
    if any(item["severity"] == "review" for item in issues):
        return "needs_review"
    if issues:
        return "advisory"
    return "passed"


def exit_code(report: dict, strict_review: bool = False) -> int:
    if report.get("status") == "failed":
        return 1
    if strict_review and report.get("status") == "needs_review":
        return 1
    return 0


def audit_layout(
    pdf: Path,
    tex: Path | None = None,
    *,
    body_end: int | None = None,
    max_ratio: float = 2.0 / 3.0,
    cap_min: int = 100,
    cap_max: int = 150,
    min_sep_chars: int = 40,
    target_min_pages: int = 21,
    target_max_pages: int = 30,
    hard_max_pages: int | None = None,
) -> dict:
    import pymupdf

    pdf = pdf.resolve()
    issues: list[dict] = []
    with pymupdf.open(pdf) as doc:
        n_pages = len(doc)
        body_pages = body_end if body_end is not None else _detect_body_end(doc)
        if body_pages < 1 or body_pages > n_pages:
            raise ValueError(f"invalid body_end={body_pages} for {n_pages} pages")

        if hard_max_pages is not None and body_pages > hard_max_pages:
            issues.append({
                "severity": "error",
                "code": "hard-page-limit",
                "detail": f"body pages {body_pages} exceed explicitly supplied hard limit {hard_max_pages}",
            })
        if body_pages < target_min_pages or body_pages > target_max_pages:
            issues.append({
                "severity": "hint",
                "code": "target-page-range",
                "detail": f"body pages {body_pages} outside inherited {target_min_pages}-{target_max_pages} target; this is not an official rule",
            })

        caption_pages: dict[tuple[str, int], int] = {}
        reference_pages: dict[tuple[str, int], int] = {}
        page_metrics = []

        for pno in range(n_pages):
            page = doc[pno]
            page_no = pno + 1
            text = page.get_text("text")
            if GARBLE_RE.search(text):
                issues.append({
                    "severity": "error",
                    "code": "garbled-glyph",
                    "page": page_no,
                    "detail": "replacement/square glyph found in PDF text layer",
                })

            paragraphs = _page_paragraphs(page)
            for _, _, block_text, _ in paragraphs:
                cap = CAP_RE.match(block_text)
                if cap:
                    caption_pages.setdefault((cap.group(1), int(cap.group(2))), page_no)
                else:
                    for ref in REF_RE.finditer(block_text):
                        reference_pages.setdefault((ref.group(1), int(ref.group(2))), page_no)

            bands = _graphics_bands(page) if page_no <= body_pages else []
            ratio = 0.0
            if bands:
                ratio = min(1.0, sum(max(0.0, b - a) for a, b in bands) / max(float(page.rect.height), 1.0))
                if ratio > max_ratio:
                    issues.append({
                        "severity": "review",
                        "code": "graphics-density",
                        "page": page_no,
                        "detail": f"graphics occupy about {ratio:.0%} of page height; inherited threshold is {max_ratio:.0%}",
                    })

                if len(bands) >= 2:
                    for (_, upper_end), (lower_start, _) in zip(bands, bands[1:]):
                        between = sum(
                            chars for y0, y1, block_text, chars in paragraphs
                            if y0 >= upper_end and y1 <= lower_start and not CAP_RE.match(block_text)
                        )
                        if between < min_sep_chars:
                            issues.append({
                                "severity": "review",
                                "code": "adjacent-graphics",
                                "page": page_no,
                                "detail": f"two graphic bands have only {between} text characters between them; inspect visual rhythm",
                            })
                            break
            page_metrics.append({"page": page_no, "graphics_height_ratio": ratio})

        for key, cap_page in sorted(caption_pages.items()):
            ref_page = reference_pages.get(key)
            if ref_page is None:
                issues.append({
                    "severity": "review",
                    "code": "unreferenced-caption",
                    "figure": f"{key[0]}{key[1]}",
                    "caption_page": cap_page,
                    "detail": "caption found but no body reference was detected",
                })
            elif abs(cap_page - ref_page) > 1:
                issues.append({
                    "severity": "review",
                    "code": "reference-distance",
                    "figure": f"{key[0]}{key[1]}",
                    "caption_page": cap_page,
                    "reference_page": ref_page,
                    "detail": "first body reference and caption are more than one page apart",
                })

        captions = extract_tex_captions(tex)
        for item in captions:
            issue = classify_caption_length(item["length"], cap_min, cap_max)
            if issue:
                issue.update({"line": item["line"]})
                issues.append(issue)

    report = {
        "pdf": str(pdf),
        "tex": str(tex.resolve()) if tex and tex.exists() else None,
        "total_pages": n_pages,
        "body_pages": body_pages,
        "heuristics": {
            "caption_length": [cap_min, cap_max],
            "target_body_pages": [target_min_pages, target_max_pages],
            "graphics_height_ratio": max_ratio,
            "minimum_text_between_graphics": min_sep_chars,
            "note": "heuristics are advisory unless an explicit hard limit is supplied",
        },
        "issues": issues,
        "pages": page_metrics,
    }
    report["status"] = _status(issues)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--tex", type=Path)
    parser.add_argument("--body-end", type=int)
    parser.add_argument("--max-ratio", type=float, default=2.0 / 3.0)
    parser.add_argument("--cap-min", type=int, default=100)
    parser.add_argument("--cap-max", type=int, default=150)
    parser.add_argument("--min-sep-chars", type=int, default=40)
    parser.add_argument("--target-min-pages", type=int, default=21)
    parser.add_argument("--target-max-pages", type=int, default=30)
    parser.add_argument("--hard-max-pages", type=int)
    parser.add_argument("--strict-review", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if not 0 < args.max_ratio <= 1:
        parser.error("--max-ratio must be in (0,1]")
    if args.cap_min < 0 or args.cap_max < args.cap_min:
        parser.error("invalid caption range")

    report = audit_layout(
        args.pdf,
        args.tex,
        body_end=args.body_end,
        max_ratio=args.max_ratio,
        cap_min=args.cap_min,
        cap_max=args.cap_max,
        min_sep_chars=args.min_sep_chars,
        target_min_pages=args.target_min_pages,
        target_max_pages=args.target_max_pages,
        hard_max_pages=args.hard_max_pages,
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "issues": len(report["issues"]), "output": str(args.output) if args.output else None}, ensure_ascii=False))
    return exit_code(report, args.strict_review)


if __name__ == "__main__":
    raise SystemExit(main())
