#!/usr/bin/env python3
"""Regression tests for verification and bookkeeping gates."""
from __future__ import annotations
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"quality_gate_{name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


pdf_audit = load_script("pdf_audit")
citation_audit = load_script("citation_audit")
workflow = load_script("workflow")


class PdfLogGateTests(unittest.TestCase):
    def test_large_overfull_is_error(self):
        issues = pdf_audit.tex_log_issues("Overfull \\hbox (39.5pt too wide) in paragraph at lines 1--2")
        self.assertTrue(any(i["code"] == "overfull-hbox" and i["severity"] == "error" for i in issues))

    def test_small_overfull_is_review(self):
        issues = pdf_audit.tex_log_issues("Overfull \\hbox (3.2pt too wide) in paragraph")
        self.assertTrue(any(i["code"] == "overfull-hbox" and i["severity"] == "review" for i in issues))

    def test_visual_review_requires_real_receipt_fields(self):
        self.assertFalse(pdf_audit.visual_review_passed({"status": "passed"}))
        self.assertTrue(pdf_audit.visual_review_passed({
            "status": "passed", "reviewer": "C", "reviewed_at": "2026-09-08T20:00:00+08:00",
            "evidence": "逐页查看渲染 PNG 与最终 PDF",
        }))


class CitationGateTests(unittest.TestCase):
    def test_numbered_references_without_body_citation_fail(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "paper.md"
            p.write_text("# 模型\n正文没有引用。\n\n# 参考文献\n[1] A. Example paper.\n", encoding="utf-8")
            report = citation_audit.audit(p)
            self.assertEqual(report["status"], "failed")
            self.assertTrue(any(i["code"] == "zero-body-citations" for i in report["issues"]))

    def test_bibtex_keyed_citation_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            paper = root / "paper.tex"
            bib = root / "refs.bib"
            paper.write_text("Result follows prior work \\cite{smith2025}.\n", encoding="utf-8")
            bib.write_text("@article{smith2025, title={X}, author={Smith}, year={2025}}\n", encoding="utf-8")
            report = citation_audit.audit(paper, bib)
            self.assertEqual(report["status"], "passed")
            self.assertEqual(report["undefined"], [])
            self.assertEqual(report["uncited"], [])


class WorkflowReconcileTests(unittest.TestCase):
    def test_later_artifact_warns_when_stage_log_lags(self):
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td)
            workflow.init(workspace, "cumcm", 2026)
            (workspace / "paper_workspace" / "draft.md").write_text("draft", encoding="utf-8")
            report = workflow.reconcile(workspace)
            self.assertFalse(report["reconcile"]["ready"])
            self.assertTrue(any(w["code"] == "bookkeeping-lag" for w in report["reconcile"]["warnings"]))


if __name__ == "__main__":
    unittest.main()
