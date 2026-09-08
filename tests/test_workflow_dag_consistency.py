"""Cross-state checks between workflow.py and task_dag.py."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import workflow
import task_dag


class WorkflowDagConsistencyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ws = Path(self.tmp.name)
        workflow.init(self.ws, "cumcm", 2026)
        (self.ws / "proof.txt").write_text("fixture", encoding="utf-8")
        self.receipt = {"status": "passed", "checks": ["fixture"],
                        "artifacts": ["proof.txt"], "issues": []}

    def _advance_to_stage3(self):
        workflow.complete(self.ws, 0, self.receipt)
        workflow.complete(self.ws, 1, self.receipt)
        workflow.complete(self.ws, 2, self.receipt)

    def test_status_reports_blocking_gated_task(self):
        self._advance_to_stage3()
        task_dag.init(self.ws, [{"id": "T-model", "role": "A", "gate_stage": 3}])
        report = workflow.status(self.ws)["dag_consistency"]
        self.assertTrue(report["present"])
        self.assertEqual(report["blocking_tasks"][0]["id"], "T-model")

    def test_stage_completion_rejects_unfinished_gated_task(self):
        self._advance_to_stage3()
        task_dag.init(self.ws, [{"id": "T-model", "role": "A", "gate_stage": 3}])
        with self.assertRaisesRegex(ValueError, "unfinished gated tasks"):
            workflow.complete(self.ws, 3, self.receipt)

    def test_done_gated_task_allows_stage_completion(self):
        self._advance_to_stage3()
        task_dag.init(self.ws, [{"id": "T-model", "role": "A", "reviewer": "B", "gate_stage": 3}])
        artifact = self.ws / "models" / "q1.md"
        artifact.parent.mkdir(parents=True)
        artifact.write_text("model", encoding="utf-8")
        r = self.ws / "task-receipt.json"
        r.write_text(json.dumps({"checks": ["reviewed"], "artifacts": ["models/q1.md"],
                                 "reviewer": "B", "reviewed_at": "2026-09-08T00:00:00Z",
                                 "evidence": "fixture"}), encoding="utf-8")
        task_dag.update(self.ws, "T-model", "done", r)
        workflow.complete(self.ws, 3, self.receipt)
        self.assertEqual(workflow.status(self.ws)["stage"], 4)

    def test_cancelled_task_is_intentional_replan_not_blocker(self):
        self._advance_to_stage3()
        task_dag.init(self.ws, [{"id": "T-model", "role": "A", "gate_stage": 3}])
        task_dag.replan(self.ws, [], ["T-model"], reason="model branch removed")
        workflow.complete(self.ws, 3, self.receipt)
        self.assertEqual(workflow.status(self.ws)["stage"], 4)


if __name__ == "__main__":
    unittest.main()
