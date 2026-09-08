#!/usr/bin/env python3
"""Competition-aware PDF checks and page rendering; visual review is still needed."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

OVERFULL_RE = re.compile(r"Overfull \\hbox .*?\((?P<pt>\d+(?:\.\d+)?)pt too wide\)", re.I)
UNDERFULL_RE = re.compile(r"Underfull \\hbox", re.I)
VISUAL_REVIEW_CODES = {"sparse-text", "image-density", "overfull-hbox", "underfull-hbox"}


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tex_log_issues(content: str):
    issues = []
    for token in ["Missing character:", "Undefined control sequence", "undefined references"]:
        if token in content:
            issues.append({"severity": "error", "code": "tex-log", "detail": token})
    overfull = [float(m.group("pt")) for m in OVERFULL_RE.finditer(content)]
    if overfull:
        worst = max(overfull)
        severity = "error" if worst > 10 else "review"
        issues.append({"severity": severity, "code": "overfull-hbox",
                       "detail": f"{len(overfull)} Overfull \\hbox warnings; worst {worst:.1f}pt too wide"})
    underfull = len(UNDERFULL_RE.findall(content))
    if underfull:
        issues.append({"severity": "review", "code": "underfull-hbox",
                       "detail": f"{underfull} Underfull \\hbox warnings; inspect affected paragraphs"})
    return issues


def visual_review_passed(review: dict | None, issues=None) -> bool:
    if not review or review.get("status") != "passed":
        return False
    if not all(review.get(k) for k in ("reviewer", "reviewed_at", "evidence")):
        return False
    unresolved_nonvisual = {i.get("code") for i in (issues or [])
                            if i.get("severity") == "review" and i.get("code") not in VISUAL_REVIEW_CODES}
    return not unresolved_nonvisual


def audit(path: Path, competition="cumcm", body_start=None, body_end=None, render_dir=None, dpi=110,
          visual_review: dict | None = None):
    import pymupdf
    path = path.resolve()
    issues = []
    with pymupdf.open(path) as doc:
        texts = [p.get_text(sort=True) for p in doc]
        n = len(doc)
        start = body_start if body_start is not None else (3 if competition == "diangong" else 2)
        appendix = None
        ai_start = None
        appendix_shared = False
        ai_shared = False
        for i, text in enumerate(texts, 1):
            lines = text.splitlines()
            app_lines = [j for j, l in enumerate(lines) if re.fullmatch(r"\s*(?:[A-Z\d]+[.、 ]\s*)?(?:附\s*录(?:\s*[A-Z一二三\d]+)?|Appendix(?:\s+[A-Z])?)\s*", l, re.I)]
            def has_body_before(j):
                return any(l.strip() and not re.fullmatch(r"[A-Z\d]+", l.strip())
                           and not re.match(r"(?:Team\s*#|Page\s+\d)", l.strip(), re.I)
                           for l in lines[:j])
            if i >= start and appendix is None and app_lines:
                appendix = i
                appendix_shared = has_body_before(app_lines[0])
            ai_lines = [j for j, l in enumerate(lines) if re.fullmatch(r"\s*Report on Use of AI\s*", l, re.I)]
            if ai_start is None and ai_lines:
                ai_start = i
                ai_shared = has_body_before(ai_lines[0])
        if competition == "mcm":
            end = body_end if body_end is not None else ((ai_start if ai_shared else ai_start - 1) if ai_start else n)
            start = 1
            limit = 25
        else:
            end = body_end if body_end is not None else ((appendix if appendix_shared else appendix - 1) if appendix else n)
            limit = 30 if competition == "cumcm" else 25
            if body_end is None and appendix is None:
                issues.append({"severity": "review", "code": "boundary", "detail": "No unambiguous appendix heading; conservatively counted to PDF end. Confirm --body-end."})
        if body_end is None and (ai_shared if competition == "mcm" else appendix_shared):
            issues.append({"severity": "review", "code": "shared-boundary", "detail": "Boundary heading shares a page with earlier text; conservatively included that page. Confirm page range."})
        if start < 1 or end < start or end > n:
            raise ValueError(f"Invalid counted page interval {start}..{end} for {n} pages")
        count = end - start + 1
        if count > limit:
            issues.append({"severity": "error", "code": "page-limit", "detail": f"Counted {count} pages > {limit}"})
        if path.stat().st_size > 20_000_000 and competition in {"cumcm", "diangong"}:
            issues.append({"severity": "error", "code": "size", "detail": "PDF exceeds conservative 20 MB threshold"})
        pages = []
        for i, page in enumerate(doc, 1):
            text = texts[i-1]
            if len(text.strip()) < 20:
                issues.append({"severity": "review", "code": "sparse-text", "page": i,
                               "detail": "Sparse/image-only page; visual inspection required"})
            if "\ufffd" in text:
                issues.append({"severity": "error", "code": "replacement-character", "page": i})
            if re.search(r"(?:MATHMODEL_[A-Z_]+|TODO|待填写|待补充)", text):
                issues.append({"severity": "error", "code": "placeholder", "page": i})
            rect = page.rect
            for block in page.get_text("blocks"):
                x0, y0, x1, y1 = block[:4]
                if x0 < -1 or y0 < -1 or x1 > rect.width + 1 or y1 > rect.height + 1:
                    issues.append({"severity": "error", "code": "off-page", "page": i})
                    break
            image_area = sum(pymupdf.Rect(im["bbox"]).get_area() for im in page.get_image_info())
            ratio = min(1.0, image_area / rect.get_area())
            if ratio > .8:
                issues.append({"severity": "review", "code": "image-density", "page": i,
                               "detail": "Image bounds cover >80%; advisory, not a contest rule"})
            pages.append({"page": i, "characters": len(text), "image_bbox_ratio": ratio})
            if render_dir:
                render_dir = Path(render_dir)
                render_dir.mkdir(parents=True, exist_ok=True)
                page.get_pixmap(dpi=dpi).save(render_dir / f"page-{i:03d}.png")
        if doc.metadata.get("author", "").strip():
            issues.append({"severity": "review", "code": "author-metadata", "detail": "Review PDF author field for identity"})
        if competition == "cumcm":
            all_text = "\n".join(texts)
            declarations = list(re.finditer(r"AI\s*工具使用声明", all_text))
            refs = list(re.finditer(r"(?m)^\s*(?:\d+[.、 ]\s*)?参考文献\s*$", all_text))
            if not declarations or not refs or declarations[-1].start() > refs[-1].start():
                issues.append({"severity": "review", "code": "ai-declaration", "detail": "Verify 2026 AI declaration heading before references"})
        log = path.with_suffix(".log")
        log_record = None
        if log.exists():
            content = log.read_text(encoding="utf-8", errors="replace")
            issues.extend(tex_log_issues(content))
            log_record = {"path": str(log.resolve()), "sha256": sha256(log)}
        has_error = any(x["severity"] == "error" for x in issues)
        if has_error:
            status = "failed"
        elif visual_review_passed(visual_review, issues):
            status = "passed"
        else:
            status = "needs_visual_review"
        return {"pdf": str(path), "pdf_sha256": sha256(path), "tex_log": log_record,
                "competition": competition, "total_pages": n,
                "counted_start": start, "counted_end": end, "counted_pages": count,
                "limit": limit, "pages": pages, "issues": issues,
                "visual_review": visual_review, "status": status}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--competition", choices=["cumcm", "mcm", "diangong"], default="cumcm")
    ap.add_argument("--body-start", type=int)
    ap.add_argument("--body-end", type=int)
    ap.add_argument("--render-dir", type=Path)
    ap.add_argument("--dpi", type=int, default=110)
    ap.add_argument("--visual-review", type=Path,
                    help="JSON receipt with status=passed, reviewer, reviewed_at and evidence; only closes visual-only review codes")
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    if not 40 <= a.dpi <= 600:
        ap.error("dpi must be 40..600")
    visual = json.loads(a.visual_review.read_text(encoding="utf-8")) if a.visual_review else None
    report = audit(a.pdf, a.competition, a.body_start, a.body_end, a.render_dir, a.dpi, visual)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "issues": len(report["issues"]), "output": str(a.output)}))
    raise SystemExit(1 if report["status"] == "failed" else 0)


if __name__ == "__main__":
    main()