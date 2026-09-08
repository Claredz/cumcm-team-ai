#!/usr/bin/env python3
"""Persistent ten-stage controller. Does not fabricate model output or human review."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAGES = ["kickoff", "problem_selection", "analysis", "model_selection", "foundation",
          "subproblem_loop", "robustness", "evaluation", "writing", "review"]


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path: Path, state: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     suffix=".tmp", delete=False) as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        temp = f.name
    os.replace(temp, path)


def load(workspace: Path):
    return json.loads((workspace / "state/decision_log.json").read_text(encoding="utf-8"))


def load_task_dag(workspace: Path):
    path = workspace / "state/task_dag.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def dag_consistency(workspace: Path, stage: int | None = None):
    """Compare workflow stage state with the execution DAG.

    decision_log.json remains authoritative for academic/stage decisions; task_dag.json
    is authoritative for task execution. Tasks may declare gate_stage=N, meaning stage N
    cannot complete until that task is done. Cancelled tasks are treated as intentionally
    removed by a recorded replan; failed/stale/planned/in_progress tasks block the gate.
    """
    dag = load_task_dag(workspace)
    if dag is None:
        return {"present": False, "issues": [], "blocking_tasks": []}
    state = load(workspace)
    current = state.get("current_stage", 0) if stage is None else stage
    tasks = dag.get("tasks", [])
    blocking = []
    issues = []
    for task in tasks:
        gate = task.get("gate_stage")
        task_status = task.get("status", "planned")
        if gate is not None and gate <= current and task_status not in ("done", "cancelled"):
            blocking.append({"id": task.get("id"), "gate_stage": gate, "status": task_status})
    if blocking:
        issues.append("DAG has unfinished tasks required by the current/target stage")

    wf = state.get("workflow", {})
    if wf.get("finished") and any(t.get("status") not in ("done", "cancelled")
                                  for t in tasks if t.get("gate_stage") is not None):
        issues.append("workflow is marked finished while gated DAG tasks remain unfinished")
    return {"present": True, "dag_version": dag.get("dag_version"),
            "issues": issues, "blocking_tasks": blocking}


def init(workspace: Path, competition: str, year: int, interaction="autonomous", formal=False):
    path = workspace / "state/decision_log.json"
    if path.exists():
        state = load(workspace)
        if state["competition"] != competition or state["problem_meta"].get("year") != year:
            raise ValueError("Existing project has another competition/year; use a separate workspace")
        return state
    state = json.loads((ROOT / "templates/shared/decision_log.json").read_text(encoding="utf-8"))
    state.update(competition=competition, started_at=now())
    state["problem_meta"]["year"] = year
    state["workflow"] = {"version": 2, "interaction": interaction, "formal_contest": formal,
                         "completed": {}, "stale": [], "team": {}, "handoff": None}
    legacy = workspace / "state/team-state.json"
    if legacy.exists():
        old = json.loads(legacy.read_text(encoding="utf-8"))
        state["workflow"]["team"] = old.get("team", {})
        state["workflow"]["migration_source"] = str(legacy)
    for name in ["state", "problem", "data/raw", "results", "figures", "paper_workspace", "support_materials", "logs/ai"]:
        (workspace / name).mkdir(parents=True, exist_ok=True)
    save(path, state)
    return state


def complete(workspace: Path, stage: int, receipt: dict):
    state = load(workspace)
    if stage != state["current_stage"] or not 0 <= stage <= 9:
        raise ValueError("Can only complete the current stage 0..9")
    if receipt.get("status") != "passed" or not receipt.get("checks"):
        raise ValueError("Receipt needs passed status and actual check evidence")
    if any(i.get("severity") == "high" for i in receipt.get("issues", [])):
        raise ValueError("Unresolved high-severity issue blocks stage completion")
    wf = state.setdefault("workflow", {"completed": {}, "stale": []})
    for key, prior in wf.get("completed", {}).items():
        if int(key) >= stage or int(key) in wf.get("stale", []):
            continue
        for item in prior["artifacts"]:
            p = workspace / item["path"]
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != item["sha256"]:
                raise ValueError(f"Upstream artifact changed; rollback and revalidate: {item['path']}")
    score_records = state.get("scores", {}).get(str(stage), [])
    if score_records and score_records[-1].get("verdict") == "block":
        raise ValueError("Latest stage score still blocks completion; repair and reassess")

    dag_check = dag_consistency(workspace, stage)
    if dag_check["present"] and dag_check["blocking_tasks"]:
        ids = ", ".join(f"{x['id']}({x['status']})" for x in dag_check["blocking_tasks"])
        raise ValueError(f"Task DAG is inconsistent with stage completion; unfinished gated tasks: {ids}")

    if wf.get("formal_contest") and stage in {1, 3, 5, 9}:
        review = receipt.get("human_review", {})
        if not all(review.get(k) for k in ("reviewer", "reviewed_at", "evidence")):
            raise ValueError("Core formal-contest checkpoint needs a real human review record")
    if not receipt.get("artifacts"):
        raise ValueError("Stage receipt needs actual artifact paths")
    artifacts = []
    for name in receipt["artifacts"]:
        p = (workspace / name).resolve()
        if not p.is_relative_to(workspace.resolve()) or not p.is_file() or p.stat().st_size == 0:
            raise ValueError(f"Missing, empty or outside-workspace artifact: {name}")
        artifacts.append({"path": str(p.relative_to(workspace.resolve())),
                          "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
    if stage == 9:
        checks = state["stages"]["9"]["compliance_checks"]
        if not all(value is True for value in checks.values()):
            raise ValueError("Final compliance checks are incomplete")
        if state.get("compliance", {}).get("ai_usage") is None:
            raise ValueError("AI usage ledger is unconfirmed")
    record = {"at": now(), "artifacts": artifacts, "receipt": receipt}
    wf["completed"][str(stage)] = record
    wf["stale"] = [s for s in wf.get("stale", []) if s != stage]
    state["current_stage"] = min(9, stage + 1)
    state["events"]["log"].append({"type": "stage_complete", "stage": stage, "at": now()})
    if stage == 9:
        wf["finished"] = True
        state["stages"]["9"]["submission_ready"] = True
    save(workspace / "state/decision_log.json", state)
    return state


def rollback(workspace: Path, stage: int, reason: str):
    state = load(workspace)
    if not reason.strip() or not 0 <= stage <= 9:
        raise ValueError("Rollback needs a stage 0..9 and a reason")
    if stage > state["current_stage"]:
        raise ValueError("Rollback cannot jump forward")
    wf = state.setdefault("workflow", {"completed": {}, "stale": []})
    wf["stale"] = sorted(set(wf.get("stale", [])) | {int(k) for k in wf["completed"] if int(k) >= stage})
    wf["finished"] = False
    state["current_stage"] = stage
    state["stages"]["9"]["submission_ready"] = False
    state["events"]["log"].append({"type": "rollback", "stage": stage, "reason": reason, "at": now()})
    save(workspace / "state/decision_log.json", state)
    return state


def _has_nonempty(workspace: Path, rel: str) -> bool:
    p = workspace / rel
    if p.is_file():
        return p.stat().st_size > 0
    if p.is_dir():
        return any(x.is_file() and x.stat().st_size > 0 for x in p.rglob("*"))
    return False


def evidence_stage(workspace: Path):
    """Infer only strong evidence that work has reached a later stage.

    Draft paper sources, trial models and ordinary result files are deliberately excluded:
    they may legitimately appear early. This is a lag detector, not an auto-stage classifier.
    """
    signals = [
        (2, "state/problem-package.json", "parsed problem package exists"),
        (2, "state/task_dag.json", "task DAG exists"),
        (6, "results/robustness/", "robustness artifacts exist"),
        (6, "runs/robustness/", "robustness artifacts exist"),
        (8, "paper_workspace/main.pdf", "compiled main PDF exists"),
        (8, "paper_output/", "paper output artifacts exist"),
        (9, "delivery/", "delivery artifacts exist"),
    ]
    found = [{"stage": stage, "path": rel, "detail": detail}
             for stage, rel, detail in signals if _has_nonempty(workspace, rel)]
    highest = max((x["stage"] for x in found), default=0)
    return highest, found


def status(workspace: Path):
    state = load(workspace)
    wf = state.get("workflow", {})
    changed = []
    for record in wf.get("completed", {}).values():
        for item in record["artifacts"]:
            p = workspace / item["path"]
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != item["sha256"]:
                changed.append(item["path"])
    s = state["current_stage"]
    reference = next((ROOT / "references").glob(f"stage_{s:02d}_*.md"))
    dag_check = dag_consistency(workspace, s)
    return {"competition": state["competition"], "stage": s, "name": STAGES[s],
            "reference": str(reference), "finished": wf.get("finished", False),
            "stale_stages": wf.get("stale", []), "changed_artifacts": sorted(set(changed)),
            "handoff": wf.get("handoff"), "interaction": wf.get("interaction", "autonomous"),
            "dag_consistency": dag_check}


def reconcile(workspace: Path):
    """Report state/DAG/artifact drift before an agent ends a work session.

    Reconcile is read-only: it never forges a stage receipt, review, or completion event.
    """
    report = status(workspace)
    highest, evidence = evidence_stage(workspace)
    warnings = []
    if highest > report["stage"] + 1:
        warnings.append({
            "code": "bookkeeping-lag",
            "detail": f"Workspace contains strong evidence reaching stage {highest}, but decision_log is at stage {report['stage']}. Complete missing stages with real receipts or rollback stale work.",
        })
    if report["changed_artifacts"]:
        warnings.append({"code": "artifact-drift", "detail": "Previously completed artifacts changed; rollback and revalidate."})
    if report["dag_consistency"]["issues"]:
        warnings.append({"code": "dag-inconsistent", "detail": "; ".join(report["dag_consistency"]["issues"])})
    report["reconcile"] = {
        "evidence_stage": highest,
        "evidence": evidence,
        "warnings": warnings,
        "ready": not warnings,
        "note": "Read-only diagnostic; stage completion still requires a real passed receipt.",
    }
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["init", "status", "next", "complete", "rollback", "reconcile"])
    ap.add_argument("--workspace", type=Path, required=True)
    ap.add_argument("--competition", choices=["cumcm", "mcm", "diangong"], default="cumcm")
    ap.add_argument("--year", type=int)
    ap.add_argument("--interaction", choices=["autonomous", "guided"], default="autonomous")
    ap.add_argument("--formal-contest", action="store_true")
    ap.add_argument("--stage", type=int)
    ap.add_argument("--receipt", type=Path)
    ap.add_argument("--reason", default="")
    args = ap.parse_args()
    try:
        if args.command == "init":
            if not args.year:
                raise ValueError("init requires --year")
            init(args.workspace, args.competition, args.year, args.interaction, args.formal_contest)
        elif args.command == "complete":
            if args.stage is None or not args.receipt:
                raise ValueError("complete requires --stage and --receipt")
            complete(args.workspace, args.stage, json.loads(args.receipt.read_text(encoding="utf-8")))
        elif args.command == "rollback":
            if args.stage is None:
                raise ValueError("rollback requires --stage")
            rollback(args.workspace, args.stage, args.reason)
        result = reconcile(args.workspace) if args.command == "reconcile" else status(args.workspace)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError) as exc:
        ap.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
