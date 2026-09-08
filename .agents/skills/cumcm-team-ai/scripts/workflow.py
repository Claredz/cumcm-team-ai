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
    return {"competition": state["competition"], "stage": s, "name": STAGES[s],
            "reference": str(reference), "finished": wf.get("finished", False),
            "stale_stages": wf.get("stale", []), "changed_artifacts": sorted(set(changed)),
            "handoff": wf.get("handoff"), "interaction": wf.get("interaction", "autonomous")}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["init", "status", "next", "complete", "rollback"])
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
        print(json.dumps(status(args.workspace), ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError) as exc:
        ap.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
