#!/usr/bin/env python3
"""Regression tests for the structural-innovation track."""
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
    spec = importlib.util.spec_from_file_location(f"structural_innovation_{name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


claim_registry = load_script("claim_registry")
final_gate = load_script("final_gate")


class InnovationClaimTests(unittest.TestCase):
    def _workspace(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        ws = Path(td.name)
        (ws / "state").mkdir()
        (ws / "runs").mkdir()
        (ws / "src").mkdir()
        (ws / "paper").mkdir()
        source = ws / "runs/compare.json"
        verifier = ws / "src/verify_compare.py"
        evidence = ws / "runs/innovation.json"
        source.write_text(json.dumps({"runtime_ratio": 0.126}), encoding="utf-8")
        verifier.write_text("assert 61.4 / 487.2 < 0.2\n", encoding="utf-8")
        evidence.write_text(json.dumps({
            "problem": "full-domain search is expensive",
            "change": "narrow the candidate region with a coarse model before exact search",
            "mechanism": "the tested approximation preserves the dominant geometry",
            "baseline": "full-domain exact search",
            "proposed": "coarse-to-fine search",
            "metrics": {
                "runtime_s": {"baseline": 487.2, "proposed": 61.4},
                "objective_gap": 0.0027
            },
            "risk": "the coarse stage may discard the global optimum region",
            "guard": "expanded region and random global probes"
        }), encoding="utf-8")
        return ws, source, verifier, evidence

    def test_verified_innovation_requires_structured_evidence(self):
        ws, _, _, _ = self._workspace()
        with self.assertRaisesRegex(ValueError, "innovation-evidence"):
            claim_registry.register(
                ws, "innovation.q3.coarse", "7.9x faster", "", "runs/compare.json", "runtime_ratio",
                status="verified", verifier="src/verify_compare.py",
                paper_refs=["paper/Q3.md#innovation"], kind="innovation",
            )

    def test_verified_innovation_is_bound_and_drift_detected(self):
        ws, _, _, evidence = self._workspace()
        record = claim_registry.register(
            ws, "innovation.q3.coarse", "7.9x faster", "", "runs/compare.json", "runtime_ratio",
            status="verified", verifier="src/verify_compare.py",
            paper_refs=["paper/Q3.md#innovation"], kind="innovation",
            innovation_evidence="runs/innovation.json",
        )
        self.assertEqual(record["kind"], "innovation")
        self.assertEqual(claim_registry.check(ws)["status"], "passed")
        evidence.write_text(json.dumps({"tampered": True}), encoding="utf-8")
        report = claim_registry.check(ws)
        self.assertEqual(report["status"], "failed")
        self.assertTrue(any(i["code"] == "evidence-drift" for i in report["issues"]))

    def test_final_gate_requires_stage8_usage_to_reference_verified_innovation(self):
        claims = {
            "claims": {
                "innovation.q3.coarse": {
                    "claim_id": "innovation.q3.coarse",
                    "kind": "innovation",
                    "status": "verified",
                    "paper_refs": ["paper/Q3.md#innovation"],
                },
                "q1.headline": {
                    "claim_id": "q1.headline",
                    "kind": "headline",
                    "status": "verified",
                    "paper_refs": ["paper/Q1.md#result"],
                }
            }
        }
        issues = []
        state = {"stages": {"8": {"innovation_claims_used": [
            {"claim_id": "innovation.q3.coarse", "paper_ref": "paper/Q3.md#innovation"}
        ]}}}
        count = final_gate.validate_paper_innovation_claims(state, claims, issues)
        self.assertEqual(count, 1)
        self.assertEqual(issues, [])

        bad_issues = []
        bad_state = {"stages": {"8": {"innovation_claims_used": [
            {"claim_id": "q1.headline", "paper_ref": "paper/Q1.md#result"}
        ]}}}
        final_gate.validate_paper_innovation_claims(bad_state, claims, bad_issues)
        self.assertTrue(any(i["code"] == "innovation-claim-wrong-kind" for i in bad_issues))


class StructuralInnovationDocsTests(unittest.TestCase):
    def test_structure_scan_precedes_solver_selection(self):
        stage2 = (ROOT / "references/stage_02_analysis.md").read_text(encoding="utf-8")
        stage3 = (ROOT / "references/stage_03_model_selection.md").read_text(encoding="utf-8")
        protocol = (ROOT / "references/structural-innovation.md").read_text(encoding="utf-8")
        self.assertIn("structure_scan", stage2)
        self.assertIn("structure → representation/formulation → approximation/decomposition → solver/algorithm", stage3)
        self.assertIn("0 个真实创新优于多个伪创新", protocol)


if __name__ == "__main__":
    unittest.main()
