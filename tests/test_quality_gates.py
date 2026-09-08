#!/usr/bin/env python3
"""Regression tests for verification and bookkeeping gates."""
from __future__ import annotations
import importlib.util
import json
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
verify_independence = load_script("verify_independence")
claim_registry = load_script("claim_registry")
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


class IndependenceGateTests(unittest.TestCase):
    def test_direct_import_of_implementation_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            impl = root / "solver.py"
            verifier = root / "verify.py"
            impl.write_text("def solve(): return 1\n", encoding="utf-8")
            verifier.write_text("import solver\nprint(solver.solve())\n", encoding="utf-8")
            report = verify_independence.audit(verifier, impl)
            self.assertEqual(report["status"], "failed")
            self.assertTrue(any(i["code"] == "imports-implementation" for i in report["issues"]))

    def test_independent_recomputation_passes_structural_guard(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            impl = root / "solver.py"
            verifier = root / "verify.py"
            impl.write_text("def solve(): return 1\n", encoding="utf-8")
            verifier.write_text('"""Independent solver check."""\nvalue = sum([1])\nassert value == 1\n', encoding="utf-8")
            report = verify_independence.audit(verifier, impl)
            self.assertEqual(report["status"], "passed")


class ClaimRegistryTests(unittest.TestCase):
    def test_verified_claim_detects_source_drift(self):
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td)
            (workspace / "state").mkdir()
            (workspace / "runs").mkdir()
            (workspace / "src").mkdir()
            source = workspace / "runs/result.json"
            impl = workspace / "src/solver.py"
            verifier = workspace / "src/verify.py"
            indep = workspace / "runs/independence.json"
            source.write_text('{"served_total":26850.57}', encoding="utf-8")
            impl.write_text("def solve(): return 26850.57\n", encoding="utf-8")
            verifier.write_text("assert abs(26850.57 - 26850.57) < 1e-9\n", encoding="utf-8")
            indep.write_text(json.dumps({"status": "passed"}), encoding="utf-8")
            claim_registry.register(
                workspace, "q3.served_total", "26850.57", "person-times",
                "runs/result.json", "served_total", status="verified",
                implementation="src/solver.py", verifier="src/verify.py",
                independence_report="runs/independence.json", paper_refs=["paper/Q3.md#result"],
            )
            self.assertEqual(claim_registry.check(workspace)["status"], "passed")
            source.write_text('{"served_total":26850.62}', encoding="utf-8")
            report = claim_registry.check(workspace)
            self.assertEqual(report["status"], "failed")
            self.assertTrue(any(i["code"] == "evidence-drift" for i in report["issues"]))


class WorkflowReconcileTests(unittest.TestCase):
    def test_final_pdf_warns_when_stage_log_lags(self):
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td)
            workflow.init(workspace, "cumcm", 2026)
            (workspace / "paper_workspace" / "main.pdf").write_bytes(b"synthetic-pdf-marker")
            report = workflow.reconcile(workspace)
            self.assertFalse(report["reconcile"]["ready"])
            self.assertTrue(any(w["code"] == "bookkeeping-lag" for w in report["reconcile"]["warnings"]))

    def test_early_paper_draft_does_not_trigger_lag(self):
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td)
            workflow.init(workspace, "cumcm", 2026)
            (workspace / "paper_workspace" / "draft.md").write_text("draft", encoding="utf-8")
            report = workflow.reconcile(workspace)
            self.assertTrue(report["reconcile"]["ready"])


if __name__ == "__main__":
    unittest.main()
