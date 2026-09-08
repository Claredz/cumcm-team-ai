#!/usr/bin/env python3
"""End-to-end regression distilled from the 2026-09-08 night-study-space dry run.

The modeling content is synthetic. The purpose is to ensure that the workflow catches
exactly the failure classes observed in the real dry run: bookkeeping lag, DAG gating,
zero body citations, TeX overflow, same-source verification, claim drift, and stale
final-gate evidence.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import citation_audit
import claim_registry
import final_gate
import pdf_audit
import task_dag
import verify_independence
import workflow


class NightStudySpaceEndToEndTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ws = Path(self.tmp.name)
        workflow.init(self.ws, "cumcm", 2026)

    def _artifact(self, rel: str, text: str = "synthetic evidence") -> str:
        p = self.ws / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return rel

    def _complete(self, stage: int, rel: str):
        self._artifact(rel, f"stage {stage} checked evidence")
        workflow.complete(
            self.ws,
            stage,
            {"status": "passed", "checks": [f"stage {stage} fixture checked"],
             "artifacts": [rel], "issues": []},
        )

    def _make_pdf(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Night study space synthetic regression paper")
        page.insert_text((72, 110), "AI 工具使用声明")
        page.insert_text((72, 150), "正文包含足够多的模拟文字，用于检查最终 PDF 的自动审计和视觉复核闭环。")
        page.insert_text((72, 200), "参考文献")
        page.insert_text((72, 230), "[1] Synthetic reference for regression testing only.")
        doc.save(path)
        doc.close()

    def test_full_quality_loop_replays_previous_failure_modes(self):
        # 1) The previous run produced a final PDF while decision_log was still at stage 0.
        marker = self.ws / "paper_workspace/main.pdf"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_bytes(b"previous-run-final-pdf-marker")
        rec = workflow.reconcile(self.ws)
        self.assertFalse(rec["reconcile"]["ready"])
        self.assertTrue(any(w["code"] == "bookkeeping-lag" for w in rec["reconcile"]["warnings"]))
        marker.unlink()

        # 2) Walk the academic controller forward with real artifact receipts.
        self._complete(0, "problem/kickoff.md")
        self._complete(1, "problem/selection.md")
        self._complete(2, "state/problem-package.json")

        # Stage 2 creates an execution DAG; an unfinished gated task must block stage 3.
        seed = [{
            "id": "TQ3-model",
            "title": "Q3 optimization contract",
            "subproblem": "Q3",
            "role": "A",
            "reviewer": "C",
            "deps": [],
            "writable_paths": ["models/Q3.md"],
            "outputs": [{"path": "models/Q3.md", "interface": "objective/variables/constraints"}],
            "acceptance": "toy case and counterexample checked",
            "gate_stage": 3,
        }]
        task_dag.init(self.ws, seed)
        self._artifact("problem/stage3-proof.md")
        with self.assertRaisesRegex(ValueError, "unfinished gated tasks"):
            workflow.complete(
                self.ws, 3,
                {"status": "passed", "checks": ["model checked"],
                 "artifacts": ["problem/stage3-proof.md"], "issues": []},
            )

        self._artifact("models/Q3.md", "Linearized Q3 contract; no bilinear sub*q term.")
        task_receipt = self.ws / "state/q3-model-receipt.json"
        task_receipt.write_text(json.dumps({
            "reviewer": "C",
            "reviewed_at": "2026-09-08T20:00:00+08:00",
            "evidence": "Checked objective, variables, constraints, and toy counterexample.",
            "checks": ["toy instance", "constraint audit"],
            "artifacts": ["models/Q3.md"],
        }), encoding="utf-8")
        task_dag.update(self.ws, "TQ3-model", "done", task_receipt)
        self._complete(3, "problem/stage3-proof.md")
        self._complete(4, "results/foundation.json")
        self._complete(5, "results/q3-solution.json")
        self._complete(6, "results/robustness/summary.json")
        self._complete(7, "results/evaluation.json")
        self._complete(8, "paper_workspace/draft-complete.txt")

        # 3) Replay the citation blind spot: 10 references and zero body citations must fail.
        paper = self.ws / "paper"
        paper.mkdir(parents=True, exist_ok=True)
        refs = "\n".join(f"[{i}] Synthetic reference {i}." for i in range(1, 11))
        paper_md = paper / "main.md"
        paper_md.write_text(f"# 模型\n正文暂时没有引用。\n\n# 参考文献\n{refs}\n", encoding="utf-8")
        citation_bad = citation_audit.audit(paper_md)
        self.assertEqual(citation_bad["status"], "failed")
        self.assertTrue(any(i["code"] == "zero-body-citations" for i in citation_bad["issues"]))

        paper_md.write_text(f"# 模型\n正文引用已有研究[1]。\n\n# 参考文献\n{refs}\n", encoding="utf-8")
        citation_ok = citation_audit.audit(paper_md)
        self.assertEqual(citation_ok["status"], "passed")
        citation_path = self.ws / "state/citation-audit.json"
        citation_path.write_text(json.dumps(citation_ok, ensure_ascii=False, indent=2), encoding="utf-8")

        # 4) Replay the 39.5pt Overfull blind spot, then repair it and close visual review.
        pdf = self.ws / "paper_workspace/main.pdf"
        self._make_pdf(pdf)
        log = pdf.with_suffix(".log")
        log.write_text("Overfull \\hbox (39.5pt too wide) in paragraph at lines 120--121\n", encoding="utf-8")
        pdf_bad = pdf_audit.audit(pdf, "cumcm", body_start=1, body_end=1)
        self.assertEqual(pdf_bad["status"], "failed")
        self.assertTrue(any(i["code"] == "overfull-hbox" and i["severity"] == "error" for i in pdf_bad["issues"]))

        log.write_text("No TeX overflow warnings in final regression fixture.\n", encoding="utf-8")
        visual = {
            "status": "passed",
            "reviewer": "C",
            "reviewed_at": "2026-09-08T20:30:00+08:00",
            "evidence": "Rendered final page inspected for clipping, overlap, and reference/declaration placement.",
        }
        pdf_ok = pdf_audit.audit(pdf, "cumcm", body_start=1, body_end=1, visual_review=visual)
        self.assertEqual(pdf_ok["status"], "passed")
        pdf_report = self.ws / "state/pdf-audit-final.json"
        pdf_report.write_text(json.dumps(pdf_ok, ensure_ascii=False, indent=2), encoding="utf-8")

        # 5) A verifier that imports the implementation must fail; an independent one may pass.
        impl = self.ws / "src/q3/solve.py"
        bad_verifier = self.ws / "src/q3/verify_bad.py"
        good_verifier = self.ws / "src/q3/verify_independent.py"
        impl.parent.mkdir(parents=True, exist_ok=True)
        impl.write_text("def solve(): return 26850.57\n", encoding="utf-8")
        bad_verifier.write_text("import solve\nassert solve.solve() > 0\n", encoding="utf-8")
        self.assertEqual(verify_independence.audit(bad_verifier, impl)["status"], "failed")
        good_verifier.write_text("recomputed = 26850.57\nassert abs(recomputed - 26850.57) < 1e-9\n", encoding="utf-8")
        indep = verify_independence.audit(good_verifier, impl)
        self.assertEqual(indep["status"], "passed")
        indep_path = self.ws / "results/q3-independence.json"
        indep_path.write_text(json.dumps(indep, indent=2), encoding="utf-8")

        # 6) Freeze the headline number in the claim registry with exact evidence hashes.
        result = self.ws / "results/q3-headline.json"
        result.write_text(json.dumps({"served_total": 26850.57}), encoding="utf-8")
        claim_registry.register(
            self.ws,
            "q3.served_total",
            "26850.57",
            "person-times",
            "results/q3-headline.json",
            "served_total",
            status="verified",
            implementation="src/q3/solve.py",
            verifier="src/q3/verify_independent.py",
            independence_report="results/q3-independence.json",
            paper_refs=["paper/main.md#模型"],
        )
        self.assertEqual(claim_registry.check(self.ws)["status"], "passed")

        # 7) Final gate is the single project-level verdict.
        state = workflow.load(self.ws)
        state["stages"]["9"]["compliance_checks"] = {
            k: True for k in state["stages"]["9"]["compliance_checks"]
        }
        state["compliance"]["ai_usage"] = []
        workflow.save(self.ws / "state/decision_log.json", state)

        gate = final_gate.build_gate(self.ws)
        self.assertEqual(gate["status"], "READY", gate["issues"])
        gate_path = self.ws / "state/final-gate.json"
        gate_path.write_text(json.dumps(gate, ensure_ascii=False, indent=2), encoding="utf-8")

        self._artifact("delivery/final-package.txt", "synthetic deliverable package")
        workflow.complete(
            self.ws,
            9,
            {"status": "passed", "checks": ["final gate READY"],
             "artifacts": ["delivery/final-package.txt"], "issues": []},
        )
        self.assertTrue(workflow.status(self.ws)["finished"])

        # 8) If a frozen result changes afterward, both provenance and stale-gate checks must fail.
        result.write_text(json.dumps({"served_total": 26850.62}), encoding="utf-8")
        self.assertEqual(claim_registry.check(self.ws)["status"], "failed")
        with self.assertRaises(ValueError):
            workflow.require_final_gate(self.ws)


if __name__ == "__main__":
    unittest.main()
