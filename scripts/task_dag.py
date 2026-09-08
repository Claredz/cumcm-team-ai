#!/usr/bin/env python3
"""Task DAG dispatcher. After stage-2 decomposition, tasks form a directed acyclic
graph assigned to team roles A/B/C. Supports replanning: structural edits bump
dag_version, upstream changes cascade staleness, nothing is silently deleted."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
ACTIVE = ("planned", "in_progress", "stale")
ROLE_DOC = "A=模型与决策 B=数据与求解 C=论证与交付；可按队员能力映射到实际人名"


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path: Path, state: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     suffix=".tmp", delete=False) as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        temp = f.name
    os.replace(temp, path)


def dag_path(workspace: Path):
    return workspace / "state/task_dag.json"


def load(workspace: Path):
    p = dag_path(workspace)
    if not p.is_file():
        raise ValueError("No task DAG here; run task_dag.py init after stage-2 decomposition")
    state = json.loads(p.read_text(encoding="utf-8"))
    validate_tasks(state["tasks"])
    return state


def task_map(tasks):
    return {t["id"]: t for t in tasks}


def topo_order(tasks):
    """Kahn's algorithm; raises on cycle. Returns order or raises ValueError."""
    ids = [t["id"] for t in tasks]
    if len(ids) != len(set(ids)):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        raise ValueError(f"Duplicate task ids: {dupes}")
    deps = {t["id"]: list(t.get("deps", [])) for t in tasks}
    for tid, d in deps.items():
        for dep in d:
            if dep not in deps:
                raise ValueError(f"{tid} depends on unknown task {dep}")
        if tid in d:
            raise ValueError(f"{tid} depends on itself")
    order, resolved = [], set()
    pending = dict(deps)
    while pending:
        progressed = False
        for tid in sorted(pending):
            if all(dep in resolved for dep in pending[tid]):
                resolved.add(tid)
                order.append(tid)
                del pending[tid]
                progressed = True
        if not progressed:
            raise ValueError(f"Task graph has a cycle among: {sorted(pending)}")
    return order


def _scope(path: str) -> PurePosixPath:
    """Normalize a repository-relative writable scope for overlap checks."""
    raw = str(path).replace("\\", "/").strip()
    if not raw:
        raise ValueError("writable_paths cannot contain an empty path")
    return PurePosixPath(raw.rstrip("/"))


def _paths_overlap(a: str, b: str) -> bool:
    pa, pb = _scope(a), _scope(b)
    return pa == pb or pa in pb.parents or pb in pa.parents


def _depends_transitively(by_id: dict, child_id: str, ancestor_id: str) -> bool:
    """Return True when child is ordered after ancestor by the DAG."""
    frontier = list(by_id[child_id].get("deps", []))
    seen = set()
    while frontier:
        tid = frontier.pop()
        if tid == ancestor_id:
            return True
        if tid in seen:
            continue
        seen.add(tid)
        frontier.extend(by_id[tid].get("deps", []))
    return False


def validate_tasks(tasks):
    topo_order(tasks)
    by_id = task_map(tasks)
    for t in tasks:
        if t.get("role") not in ("A", "B", "C"):
            raise ValueError(f"{t['id']}: role must be A, B or C ({ROLE_DOC})")
        if t.get("reviewer") and t["reviewer"] == t.get("role"):
            raise ValueError(f"{t['id']}: reviewer must differ from the assigned role (cross-check)")
        gate = t.get("gate_stage")
        if gate is not None and (not isinstance(gate, int) or not 0 <= gate <= 9):
            raise ValueError(f"{t['id']}: gate_stage must be null or an integer 0..9")

    # Single-writer means no concurrently executable active tasks may own overlapping
    # scopes. Parent/child scopes are therefore conflicts unless the DAG orders the
    # two tasks, in which case the earlier writer has already handed off before the
    # later task becomes ready.
    active = [t for t in tasks if t.get("status", "planned") in ACTIVE]
    for i, left in enumerate(active):
        for right in active[i + 1:]:
            ordered = (_depends_transitively(by_id, left["id"], right["id"])
                       or _depends_transitively(by_id, right["id"], left["id"]))
            if ordered:
                continue
            for a in left.get("writable_paths", []):
                for b in right.get("writable_paths", []):
                    if _paths_overlap(a, b):
                        raise ValueError(
                            f"Single-writer conflict on overlapping scopes {a} vs {b}: "
                            f"{left['id']} vs {right['id']}"
                        )


def cascade_stale(tasks, changed_ids, reason, events):
    """Mark changed tasks and all transitive downstream as stale; preserve done artifacts.
    Already-stale or cancelled nodes keep their status; stale nodes still propagate downstream."""
    by_id = task_map(tasks)
    frontier = list(changed_ids)
    processed = set()
    while frontier:
        tid = frontier.pop()
        if tid in processed:
            continue
        processed.add(tid)
        t = by_id[tid]
        if t.get("status") != "stale":
            t["history"].append({"at": now(), "from": t.get("status"), "to": "stale", "reason": reason})
            t["status"] = "stale"
        for t2 in tasks:
            if tid in t2.get("deps", []) and t2["id"] not in processed and t2.get("status") != "cancelled":
                if t2.get("status") != "stale":
                    t2["history"].append({"at": now(), "from": t2.get("status"), "to": "stale",
                                          "reason": f"upstream {tid} invalidated"})
                    t2["status"] = "stale"
                frontier.append(t2["id"])
    events.append({"type": "invalidate", "tasks": sorted(processed), "reason": reason, "at": now()})
    return sorted(processed)


def ready_tasks(tasks):
    by_id = task_map(tasks)
    return [t for t in tasks
            if t.get("status") in ("planned", "stale")
            and all(by_id[d].get("status") == "done" for d in t.get("deps", []))]


def _dependency_spec(dep: dict, qi: str):
    """Return (model_upstreams, result_upstreams) with legacy-list compatibility.

    New Stage-2 records use:
      {"model_depends_on": [...], "result_depends_on": [...]}
    A legacy list means both model and result dependency, preserving the old model
    ordering while fixing the missing result gate.
    """
    raw = dep.get(qi, [])
    if isinstance(raw, list):
        model, result = raw, raw
    elif isinstance(raw, dict):
        model = raw.get("model_depends_on", [])
        result = raw.get("result_depends_on", [])
    else:
        raise ValueError(f"{qi}: dependency must be a list or an object")
    for label, values in (("model_depends_on", model), ("result_depends_on", result)):
        if not isinstance(values, list) or any(not isinstance(x, str) or not x for x in values):
            raise ValueError(f"{qi}.{label} must be a list of subproblem IDs")
        if qi in values:
            raise ValueError(f"{qi}.{label} cannot depend on itself")
    return list(dict.fromkeys(model)), list(dict.fromkeys(result))


def init(workspace: Path, seed: list | None):
    log_path = workspace / "state/decision_log.json"
    if seed is None:
        if not log_path.is_file():
            raise ValueError("init needs either --seed-file or a decision_log.json from stage 2")
        log = json.loads(log_path.read_text(encoding="utf-8"))
        dep = log.get("stages", {}).get("2", {}).get("subproblem_dependency") or {}
        qis = sorted(dep) if dep else []
        if not qis:
            raise ValueError("Stage-2 decomposition not found; DAG dispatch starts after problem analysis")
        seed = seed_from_subproblems(qis, dep)
    seed = [normalize_new(t) for t in seed]
    validate_tasks(seed)
    state = {"schema_version": 2, "dag_version": 1, "created_from_stage": 2,
             "_role_doc": ROLE_DOC, "tasks": seed, "events": [
                 {"type": "init", "tasks": len(seed), "at": now()}]}
    save(dag_path(workspace), state)
    return state


def seed_from_subproblems(qis, dep):
    """Default skeleton: per-Qi model(A)->solve(B)->verify(cross)->write(C), plus shared roots.
    The AI/team refines this via add/replan; it is a starting point, not a mandate."""
    tasks = [
        {"id": "T0-foundation", "title": "假设、符号、单位与数据口径", "subproblem": "*",
         "role": "A", "reviewer": "C", "deps": [], "writable_paths": ["models/foundation.md"],
         "outputs": [{"path": "models/foundation.md", "interface": "符号/单位表"}],
         "acceptance": "符号唯一、单位可追溯、与题面一致", "status": "planned", "history": [],
         "gate_stage": None},
        {"id": "T0-datacheck", "title": "原始数据检查与基线数据集", "subproblem": "*",
         "role": "B", "reviewer": "A", "deps": [], "writable_paths": ["data/processed/", "src/"],
         "outputs": [{"path": "data/processed/", "interface": "清洗后数据+处理记录"}],
         "acceptance": "数据字典完整、指纹可复现", "status": "planned", "history": [],
         "gate_stage": None},
        {"id": "T0-skeleton", "title": "论文骨架与证据目录", "subproblem": "*",
         "role": "C", "reviewer": "B", "deps": [], "writable_paths": ["paper/"],
         "outputs": [{"path": "paper/", "interface": "章节骨架+证据索引"}],
         "acceptance": "覆盖全部子问题、无未运行结论", "status": "planned", "history": [],
         "gate_stage": None},
    ]
    for qi in qis:
        model_upstreams, result_upstreams = _dependency_spec(dep, qi)
        unknown = sorted((set(model_upstreams) | set(result_upstreams)) - set(qis))
        if unknown:
            raise ValueError(f"{qi}: dependency refers to unknown subproblems: {unknown}")
        model_deps = [f"T{p}-model" for p in model_upstreams]
        result_deps = [f"T{p}-verify" for p in result_upstreams]
        verify_reviewer = "A" if qi != "Q1" else "C"
        tasks += [
            {"id": f"T{qi}-model", "title": f"{qi} 模型合同与选型", "subproblem": qi, "role": "A",
             "reviewer": "C", "deps": ["T0-foundation"] + model_deps,
             "writable_paths": [f"models/{qi}.md"],
             "outputs": [{"path": f"models/{qi}.md", "interface": "目标/变量/约束/接口"}],
             "acceptance": "toy 小样例通过、反例检验", "status": "planned", "history": [],
             "gate_stage": 3},
            {"id": f"T{qi}-solve", "title": f"{qi} 实现与求解", "subproblem": qi, "role": "B",
             "reviewer": "A", "deps": [f"T{qi}-model", "T0-datacheck"] + result_deps,
             "writable_paths": [f"src/{qi}/", f"runs/{qi}/"],
             "outputs": [{"path": f"runs/{qi}/", "interface": "结果表+日志+run_id"}],
             "acceptance": "复现命令可跑、约束满足、误差在限", "status": "planned", "history": [],
             "gate_stage": 5},
            {"id": f"T{qi}-verify", "title": f"{qi} 结果交叉复核", "subproblem": qi,
             "role": verify_reviewer, "reviewer": "B",
             "deps": [f"T{qi}-solve"],
             "writable_paths": [f"runs/{qi}/review.md"],
             "outputs": [{"path": f"runs/{qi}/review.md", "interface": "复核结论+证据"}],
             "acceptance": "关键数值独立复算一致", "status": "planned", "history": [],
             "gate_stage": 5},
            {"id": f"T{qi}-write", "title": f"{qi} 论文章节", "subproblem": qi, "role": "C",
             "reviewer": "A", "deps": [f"T{qi}-verify", "T0-skeleton"],
             "writable_paths": [f"paper/sections/{qi}/"],
             "outputs": [{"path": f"paper/sections/{qi}/", "interface": "成稿章节"}],
             "acceptance": "数值与 runs 一致、引用真实", "status": "planned", "history": [],
             "gate_stage": 8},
        ]
    tasks += [
        {"id": "T9-robust", "title": "全局稳健性", "subproblem": "*", "role": "B", "reviewer": "A",
         "deps": [f"T{qi}-verify" for qi in qis], "writable_paths": ["runs/robustness/"],
         "outputs": [{"path": "runs/robustness/", "interface": "扰动区间+结论"}],
         "acceptance": "有依据的扰动、结论稳定", "status": "planned", "history": [],
         "gate_stage": 6},
        {"id": "T9-abstract", "title": "摘要与终稿整合", "subproblem": "*", "role": "C", "reviewer": "A",
         "deps": ["T9-robust", "T0-skeleton"] + [f"T{qi}-write" for qi in qis],
         "writable_paths": ["paper/abstract.md", "delivery/"],
         "outputs": [{"path": "paper/abstract.md", "interface": "终摘要"}],
         "acceptance": "摘要数值可溯源、合规检查通过", "status": "planned", "history": [],
         "gate_stage": 8},
    ]
    return tasks


def normalize_new(raw: dict) -> dict:
    t = {"id": raw["id"], "title": raw.get("title", ""), "subproblem": raw.get("subproblem", "*"),
         "role": raw["role"], "reviewer": raw.get("reviewer"),
         "deps": list(raw.get("deps", [])),
         "writable_paths": list(raw.get("writable_paths", [])),
         "outputs": list(raw.get("outputs", [])),
         "acceptance": raw.get("acceptance", ""), "status": "planned", "history": [],
         "gate_stage": raw.get("gate_stage")}
    if not t["reviewer"]:
        t["reviewer"] = {"A": "B", "B": "C", "C": "A"}[t["role"]]
    return t


def add(workspace: Path, tasks_raw: list):
    state = load(workspace)
    by_id = task_map(state["tasks"])
    for raw in tasks_raw:
        if raw["id"] in by_id:
            raise ValueError(f"Task {raw['id']} already exists; use replan to change it")
        state["tasks"].append(normalize_new(raw))
    validate_tasks(state["tasks"])
    state["dag_version"] += 1
    state["events"].append({"type": "add", "tasks": [t["id"] for t in tasks_raw], "at": now()})
    save(dag_path(workspace), state)
    return state


def replan(workspace: Path, tasks_raw: list, cancel: list, reason: str):
    """Structural edit: add new tasks, update fields of existing ones, optionally cancel.
    Completed tasks are never silently dropped; changing an upstream task's deps/outputs
    requires an explicit invalidate call for the downstream cascade."""
    if not reason.strip():
        raise ValueError("replan needs a reason (recorded in events)")
    state = load(workspace)
    by_id = task_map(state["tasks"])
    for raw in tasks_raw:
        if raw["id"] in by_id:
            t = by_id[raw["id"]]
            t["history"].append({"at": now(), "change": {k: raw[k] for k in ("deps", "outputs", "writable_paths", "title", "gate_stage") if k in raw},
                                 "reason": reason})
            for k in ("title", "subproblem", "reviewer", "acceptance", "gate_stage"):
                if k in raw:
                    t[k] = raw[k]
            for k in ("deps", "writable_paths", "outputs"):
                if k in raw:
                    t[k] = list(raw[k])
            if "role" in raw and raw["role"] != t["role"]:
                raise ValueError(f"{raw['id']}: reassigning role mid-flight needs cancel + new task for clean handoff")
        else:
            state["tasks"].append(normalize_new(raw))
    for cid in cancel:
        if cid not in by_id:
            raise ValueError(f"Cannot cancel unknown task {cid}")
        t = by_id[cid]
        if t.get("status") == "done":
            raise ValueError(f"{cid} is done; invalidate it instead so downstream is cascaded")
        t["history"].append({"at": now(), "from": t.get("status"), "to": "cancelled", "reason": reason})
        t["status"] = "cancelled"
    validate_tasks(state["tasks"])
    state["dag_version"] += 1
    state["events"].append({"type": "replan", "added": [t["id"] for t in tasks_raw if t["id"] not in by_id],
                            "updated": [t["id"] for t in tasks_raw if t["id"] in by_id],
                            "cancelled": cancel, "reason": reason, "at": now()})
    save(dag_path(workspace), state)
    return state


def update(workspace: Path, task_id: str, status: str, receipt_path: Path | None):
    if status not in ("in_progress", "done", "failed"):
        raise ValueError("update supports in_progress | done | failed")
    state = load(workspace)
    by_id = task_map(state["tasks"])
    if task_id not in by_id:
        raise ValueError(f"Unknown task {task_id}")
    t = by_id[task_id]
    if t.get("status") == "cancelled":
        raise ValueError(f"{task_id} is cancelled; replan a replacement")
    if status == "in_progress":
        blocked = [d for d in t.get("deps", []) if by_id[d].get("status") != "done"]
        if blocked:
            raise ValueError(f"{task_id} blocked by unfinished deps: {blocked}")
    if status == "done":
        blocked = [d for d in t.get("deps", []) if by_id[d].get("status") != "done"]
        if blocked:
            raise ValueError(f"{task_id} blocked by unfinished deps: {blocked}")
        if not receipt_path or not receipt_path.is_file():
            raise ValueError("done requires --receipt (checks, artifacts, reviewer evidence)")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if receipt.get("reviewer") != t.get("reviewer"):
            raise ValueError(f"receipt reviewer must be {t.get('reviewer')} (cross-check, differs from role {t.get('role')})")
        if not receipt.get("reviewed_at") or not receipt.get("evidence"):
            raise ValueError("receipt needs reviewed_at and evidence of the cross-check")
        if not receipt.get("checks") or not receipt.get("artifacts"):
            raise ValueError("receipt needs actual checks and artifact paths")
        artifacts = []
        for name in receipt["artifacts"]:
            p = (workspace / name).resolve()
            if not p.is_relative_to(workspace.resolve()) or not p.is_file() or p.stat().st_size == 0:
                raise ValueError(f"Missing, empty or outside-workspace artifact: {name}")
            artifacts.append({"path": str(p.relative_to(workspace.resolve())),
                              "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
        t["artifacts"] = artifacts
    t["history"].append({"at": now(), "from": t.get("status"), "to": status})
    t["status"] = status
    if status == "failed":
        state["events"].append({"type": "task_failed", "task": task_id, "at": now()})
    else:
        state["events"].append({"type": "task_update", "task": task_id, "to": status, "at": now()})
    save(dag_path(workspace), state)
    return state


def invalidate(workspace: Path, task_ids: list, reason: str):
    if not reason.strip():
        raise ValueError("invalidate needs a reason (what upstream result changed)")
    state = load(workspace)
    by_id = task_map(state["tasks"])
    for tid in task_ids:
        if tid not in by_id:
            raise ValueError(f"Unknown task {tid}")
    touched = cascade_stale(state["tasks"], task_ids, reason, state["events"])
    save(dag_path(workspace), state)
    return {"invalidated": touched}


def board(workspace: Path):
    state = load(workspace)
    ready = ready_tasks(state["tasks"])
    by_id = task_map(state["tasks"])
    blocked = {t["id"]: [d for d in t.get("deps", []) if by_id[d].get("status") != "done"]
               for t in state["tasks"] if t.get("status") in ("planned", "stale") and t not in ready}
    return {"dag_version": state["dag_version"],
            "ready": [{"id": t["id"], "title": t["title"], "role": t["role"],
                       "reviewer": t.get("reviewer"), "subproblem": t.get("subproblem"),
                       "status": t["status"], "acceptance": t.get("acceptance", ""),
                       "gate_stage": t.get("gate_stage")} for t in ready],
            "in_progress": [{"id": t["id"], "role": t["role"], "gate_stage": t.get("gate_stage")}
                            for t in state["tasks"] if t.get("status") == "in_progress"],
            "blocked": [{"id": k, "waiting_on": v} for k, v in blocked.items()],
            "done": [t["id"] for t in state["tasks"] if t.get("status") == "done"],
            "failed": [t["id"] for t in state["tasks"] if t.get("status") == "failed"],
            "stale": [t["id"] for t in state["tasks"] if t.get("status") == "stale"],
            "cancelled": [t["id"] for t in state["tasks"] if t.get("status") == "cancelled"]}


def check_artifacts(workspace: Path):
    """Done tasks whose output files changed since completion should be invalidated."""
    state = load(workspace)
    drifted = []
    for t in state["tasks"]:
        if t.get("status") != "done":
            continue
        for a in t.get("artifacts", []):
            p = workspace / a["path"]
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != a["sha256"]:
                drifted.append({"task": t["id"], "artifact": a["path"]})
    return {"drifted": drifted,
            "advice": "run invalidate --task <id> to cascade staleness, then redo the task" if drifted else ""}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["init", "add", "replan", "update", "invalidate", "board", "check"])
    ap.add_argument("--workspace", type=Path, required=True)
    ap.add_argument("--seed-file", type=Path, help="JSON array of seed tasks (default: derive from stage-2 decomposition)")
    ap.add_argument("--tasks", type=Path, help="JSON file with {tasks: [...], cancel: [...]} or an array")
    ap.add_argument("--task", help="task id for update/invalidate")
    ap.add_argument("--status", choices=["in_progress", "done", "failed"])
    ap.add_argument("--receipt", type=Path)
    ap.add_argument("--reason", default="")
    args = ap.parse_args()
    try:
        if args.command == "init":
            seed = json.loads(args.seed_file.read_text(encoding="utf-8")) if args.seed_file else None
            out = init(args.workspace, seed)
        elif args.command == "add":
            if not args.tasks:
                raise ValueError("add requires --tasks file")
            raw = json.loads(args.tasks.read_text(encoding="utf-8"))
            out = add(args.workspace, raw if isinstance(raw, list) else raw.get("tasks", []))
        elif args.command == "replan":
            if not args.tasks:
                raise ValueError("replan requires --tasks file")
            raw = json.loads(args.tasks.read_text(encoding="utf-8"))
            tasks = raw.get("tasks", []) if isinstance(raw, dict) else raw
            cancel = raw.get("cancel", []) if isinstance(raw, dict) else []
            out = replan(args.workspace, tasks, cancel, args.reason)
        elif args.command == "update":
            if not args.task or not args.status:
                raise ValueError("update requires --task and --status")
            out = update(args.workspace, args.task, args.status, args.receipt)
        elif args.command == "invalidate":
            if not args.task:
                raise ValueError("invalidate requires --task (repeatable ids comma-separated)")
            out = invalidate(args.workspace, [x.strip() for x in args.task.split(",")], args.reason)
        elif args.command == "board":
            out = board(args.workspace)
        else:
            out = check_artifacts(args.workspace)
        print(json.dumps(out, ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError) as exc:
        ap.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
