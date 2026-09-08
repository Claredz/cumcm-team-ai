#!/usr/bin/env python3
"""Competition-aware PDF checks and page rendering; visual review is still needed."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path


def audit(path: Path, competition="cumcm", body_start=None, body_end=None, render_dir=None, dpi=110):
    import pymupdf
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
        if log.exists():
            content = log.read_text(encoding="utf-8", errors="replace")
            for token in ["Missing character:", "Undefined control sequence", "undefined references"]:
                if token in content:
                    issues.append({"severity": "error", "code": "tex-log", "detail": token})
        return {"pdf": str(path), "competition": competition, "total_pages": n,
                "counted_start": start, "counted_end": end, "counted_pages": count,
                "limit": limit, "pages": pages, "issues": issues,
                "status": "failed" if any(x["severity"] == "error" for x in issues) else "needs_visual_review"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--competition", choices=["cumcm", "mcm", "diangong"], default="cumcm")
    ap.add_argument("--body-start", type=int)
    ap.add_argument("--body-end", type=int)
    ap.add_argument("--render-dir", type=Path)
    ap.add_argument("--dpi", type=int, default=110)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    if not 40 <= a.dpi <= 600:
        ap.error("dpi must be 40..600")
    report = audit(a.pdf, a.competition, a.body_start, a.body_end, a.render_dir, a.dpi)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "issues": len(report["issues"]), "output": str(a.output)}))
    raise SystemExit(1 if report["status"] == "failed" else 0)


if __name__ == "__main__":
    main()
