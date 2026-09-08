#!/usr/bin/env python3
"""Task DAG dispatcher tests: acyclicity, dispatch gating, replanning, invalidation cascade."""

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
    spec = importlib.util.spec_from_file_location(f"mathmodel_test_{name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


task_dag = load_script("task_dag")


def make_log(workspace: Path, dep: dict):
    log = {"stages": {"2": {"subproblem_dependency": dep}}}
    p = workspace / "state/decision_log.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(log), encoding="utf-8")


def receipt(workspace: Path, reviewer: str, artifacts: list) -> Path:
    r = {"status": "passed", "checks": ["数值复算一致"], "artifacts": artifacts,
         "reviewer": reviewer, "reviewed_at": "2026-09-08T00:00:00Z", "evidence": "独立复算"}
    p = workspace / "receipt.json"
    p.write_text(json.dumps(r), encoding="utf-8")
    return p


def artifact_file(workspace: Path, rel: str) -> str:
    p = workspace / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("result 42", encoding="utf-8")
    return rel


class TaskDagTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ws = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_init_from_stage2_dependency(self):
        make_log(self.ws, {"Q1": [], "Q2": ["Q1"]})
        state = task_dag.init(self.ws, None)
        ids = {t["id"] for t in state["tasks"]}
        self.assertIn("TQ1-solve", ids)
        self.assertIn("TQ2-model", ids)
        q2_model = next(t for t in state["tasks"] if t["id"] == "TQ2-model")
        q2_solve = next(t for t in state["tasks"] if t["id"] == "TQ2-solve")
        self.assertEqual(q2_model["deps"], ["T0-foundation", "TQ1-model"])
        self.assertIn("TQ1-verify", q2_solve["deps"])

    def test_structured_dependency_distinguishes_model_and_result_edges(self):
        make_log(self.ws, {
            "Q1": {"model_depends_on": [], "result_depends_on": []},
            "Q2": {"model_depends_on": [], "result_depends_on": ["Q1"]},
        })
        state = task_dag.init(self.ws, None)
        by_id = {t["id"]: t for t in state["tasks"]}
        self.assertNotIn("TQ1-model", by_id["TQ2-model"]["deps"])
        self.assertIn("TQ1-verify", by_id["TQ2-solve"]["deps"])

    def test_unknown_structured_dependency_is_rejected(self):
        make_log(self.ws, {
            "Q1": {"model_depends_on": [], "result_depends_on": ["Q9"]},
        })
        with self.assertRaisesRegex(ValueError, "unknown subproblems"):
            task_dag.init(self.ws, None)

    def test_init_requires_stage2(self):
        make_log(self.ws, {})
        with self.assertRaises(ValueError):
            task_dag.init(self.ws, None)

    def test_cycle_rejected(self):
        seed = [
            {"id": "T1", "role": "A", "deps": ["T2"]},
            {"id": "T2", "role": "B", "deps": ["T1"]},
        ]
        with self.assertRaises(ValueError):
            task_dag.init(self.ws, seed)

    def test_dangling_dep_rejected(self):
        with self.assertRaises(ValueError):
            task_dag.init(self.ws, [{"id": "T1", "role": "A", "deps": ["T9"]}])

    def test_single_writer_conflict_rejected(self):
        seed = [
            {"id": "T1", "role": "A", "writable_paths": ["paper/"]},
            {"id": "T2", "role": "C", "writable_paths": ["paper/"]},
        ]
        with self.assertRaises(ValueError):
            task_dag.init(self.ws, seed)

    def test_nested_single_writer_conflict_rejected_when_concurrent(self):
        seed = [
            {"id": "T1", "role": "A", "writable_paths": ["paper/"]},
            {"id": "T2", "role": "C", "writable_paths": ["paper/sections/Q1/"]},
        ]
        with self.assertRaisesRegex(ValueError, "overlapping scopes"):
            task_dag.init(self.ws, seed)

    def test_nested_single_writer_allowed_when_dependency_orders_handoff(self):
        seed = [
            {"id": "T1", "role": "A", "writable_paths": ["paper/"]},
            {"id": "T2", "role": "C", "deps": ["T1"], "writable_paths": ["paper/sections/Q1/"]},
        ]
        state = task_dag.init(self.ws, seed)
        self.assertEqual(len(state["tasks"]), 2)

    def test_disjoint_sibling_paths_are_allowed(self):
        seed = [
            {"id": "T1", "role": "A", "writable_paths": ["src/Q1/"]},
            {"id": "T2", "role": "B", "writable_paths": ["src/Q2/"]},
        ]
        state = task_dag.init(self.ws, seed)
        self.assertEqual(len(state["tasks"]), 2)

    def test_self_review_rejected(self):
        seed = [{"id": "T1", "role": "A", "reviewer": "A"}]
        with self.assertRaises(ValueError):
            task_dag.init(self.ws, seed)

    def test_dispatch_gating_and_done_requires_cross_receipt(self):
        task_dag.init(self.ws, [{"id": "T1", "role": "A", "writable_paths": ["models/"]},
                                {"id": "T2", "role": "B", "deps": ["T1"]}])
        with self.assertRaises(ValueError):
            task_dag.update(self.ws, "T2", "in_progress", None)
        with self.assertRaises(ValueError):
            task_dag.update(self.ws, "T1", "done", None)
        rel = artifact_file(self.ws, "models/m.md")
        with self.assertRaises(ValueError):
            task_dag.update(self.ws, "T1", "done", receipt(self.ws, "A", [rel]))
        task_dag.update(self.ws, "T1", "done", receipt(self.ws, "B", [rel]))
        task_dag.update(self.ws, "T2", "in_progress", None)
        b = task_dag.board(self.ws)
        self.assertEqual(b["done"], ["T1"])
        self.assertEqual([t["id"] for t in b["in_progress"]], ["T2"])

    def test_invalidate_cascades_downstream_not_sideways(self):
        task_dag.init(self.ws, [
            {"id": "T1", "role": "A"},
            {"id": "T2", "role": "B", "deps": ["T1"]},
            {"id": "T3", "role": "C", "deps": ["T2"]},
            {"id": "T4", "role": "A", "deps": []},
        ])
        out = task_dag.invalidate(self.ws, ["T1"], "Q1 模型假设变化")
        self.assertEqual(out["invalidated"], ["T1", "T2", "T3"])
        state = task_dag.load(self.ws)
        by_id = {t["id"]: t for t in state["tasks"]}
        self.assertEqual(by_id["T4"]["status"], "planned")
        self.assertEqual(by_id["T3"]["status"], "stale")
        self.assertTrue(all("history" in t for t in state["tasks"]))

    def test_reinvalidate_through_already_stale_node_still_propagates(self):
        task_dag.init(self.ws, [
            {"id": "T1", "role": "A"},
            {"id": "T2", "role": "B", "deps": ["T1"]},
            {"id": "T3", "role": "C", "deps": ["T2"]},
        ])
        task_dag.invalidate(self.ws, ["T2"], "上游 T2 先失效")
        out = task_dag.invalidate(self.ws, ["T1"], "T1 也失效")
        self.assertEqual(out["invalidated"], ["T1", "T2", "T3"])
        state = task_dag.load(self.ws)
        t3 = next(t for t in state["tasks"] if t["id"] == "T3")
        self.assertEqual(t3["status"], "stale")
        t2 = next(t for t in state["tasks"] if t["id"] == "T2")
        stale_entries = [h for h in t2["history"] if h.get("to") == "stale"]
        self.assertEqual(len(stale_entries), 1)

    def test_diamond_dependency_cascade(self):
        task_dag.init(self.ws, [
            {"id": "T1", "role": "A"},
            {"id": "T2", "role": "B", "deps": ["T1"]},
            {"id": "T3", "role": "C", "deps": ["T1"]},
            {"id": "T4", "role": "A", "deps": ["T2", "T3"]},
        ])
        out = task_dag.invalidate(self.ws, ["T1"], "根任务失效")
        self.assertEqual(out["invalidated"], ["T1", "T2", "T3", "T4"])
        t4 = next(t for t in task_dag.load(self.ws)["tasks"] if t["id"] == "T4")
        self.assertEqual(len([h for h in t4["history"] if h.get("to") == "stale"]), 1)

    def test_replan_add_update_cancel_with_version_bump(self):
        task_dag.init(self.ws, [{"id": "T1", "role": "A"}, {"id": "T2", "role": "B", "deps": ["T1"]}])
        task_dag.replan(self.ws, [
            {"id": "T3", "role": "C", "deps": ["T1"]},
            {"id": "T2", "title": "Q1 求解（改用启发式）", "deps": ["T1", "T3"]},
        ], cancel=["T1"], reason="发现 Q1 可独立于基础层")
        state = task_dag.load(self.ws)
        self.assertEqual(state["dag_version"], 2)
        by_id = {t["id"]: t for t in state["tasks"]}
        self.assertEqual(by_id["T2"]["deps"], ["T1", "T3"])
        self.assertEqual(by_id["T1"]["status"], "cancelled")

    def test_role_reassignment_refused(self):
        task_dag.init(self.ws, [{"id": "T1", "role": "A"}])
        with self.assertRaises(ValueError):
            task_dag.replan(self.ws, [{"id": "T1", "role": "B"}], [], reason="换人")

    def test_artifact_drift_detection(self):
        task_dag.init(self.ws, [{"id": "T1", "role": "A", "writable_paths": ["models/"]}])
        rel = artifact_file(self.ws, "models/m.md")
        task_dag.update(self.ws, "T1", "done", receipt(self.ws, "B", [rel]))
        self.assertEqual(task_dag.check_artifacts(self.ws)["drifted"], [])
        (self.ws / rel).write_text("result 43", encoding="utf-8")
        drifted = task_dag.check_artifacts(self.ws)["drifted"]
        self.assertEqual(len(drifted), 1)
        self.assertEqual(drifted[0]["task"], "T1")

    def test_done_task_cannot_be_cancelled_only_invalidated(self):
        task_dag.init(self.ws, [{"id": "T1", "role": "A"}])
        rel = artifact_file(self.ws, "models/m.md")
        task_dag.update(self.ws, "T1", "done", receipt(self.ws, "B", [rel]))
        with self.assertRaises(ValueError):
            task_dag.replan(self.ws, [], cancel=["T1"], reason="删掉")
        out = task_dag.invalidate(self.ws, ["T1"], "输入数据修正")
        self.assertEqual(out["invalidated"], ["T1"])


if __name__ == "__main__":
    unittest.main()
