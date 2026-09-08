#!/usr/bin/env python3
"""Trace paper claims to frozen result files and independent verification evidence.

Headline claims bind reported values to source fields. Innovation claims additionally
bind a structured baseline/proposed comparison so model-name novelty cannot masquerade
as verified innovation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

CLAIM_KINDS = {"headline", "innovation"}
INNOVATION_REQUIRED = ("problem", "change", "mechanism", "baseline", "proposed", "metrics", "risk", "guard")


def now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def registry_path(workspace: Path):
    return workspace / "state/claims.json"


def load(workspace: Path):
    p = registry_path(workspace)
    if not p.exists():
        return {"schema_version": 2, "claims": {}, "history": []}
    state = json.loads(p.read_text(encoding="utf-8"))
    state.setdefault("schema_version", 1)
    state.setdefault("claims", {})
    state.setdefault("history", [])
    return state


def save(workspace: Path, state: dict):
    p = registry_path(workspace)
    p.parent.mkdir(parents=True, exist_ok=True)
    state["schema_version"] = max(int(state.get("schema_version", 1)), 2)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=p.parent, suffix=".tmp", delete=False) as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        temp = f.name
    os.replace(temp, p)


def safe_file(workspace: Path, rel: str):
    p = (workspace / rel).resolve()
    root = workspace.resolve()
    if not p.is_relative_to(root) or not p.is_file() or p.stat().st_size == 0:
        raise ValueError(f"Missing, empty or outside-workspace evidence file: {rel}")
    return p


def file_record(workspace: Path, rel: str):
    p = safe_file(workspace, rel)
    return {"path": str(p.relative_to(workspace.resolve())), "sha256": sha256(p)}


def _load_json_record(workspace: Path, record: dict):
    p = safe_file(workspace, record["path"])
    return json.loads(p.read_text(encoding="utf-8"))


def _load_independence_report(workspace: Path, record: dict):
    return _load_json_record(workspace, record)


def _validate_independence_binding(report: dict, verifier_rec: dict, implementation_rec: dict):
    if report.get("status") != "passed":
        raise ValueError("independence report must have status=passed")
    if report.get("verifier_sha256") != verifier_rec.get("sha256"):
        raise ValueError("independence report does not match the registered verifier SHA256")
    if report.get("implementation_sha256") != implementation_rec.get("sha256"):
        raise ValueError("independence report does not match the registered implementation SHA256")


def _validate_innovation_evidence(data: dict):
    if not isinstance(data, dict):
        raise ValueError("innovation evidence must be a JSON object")
    missing = [k for k in INNOVATION_REQUIRED if k not in data]
    if missing:
        raise ValueError(f"innovation evidence missing required fields: {missing}")
    for key in ("problem", "change", "mechanism", "baseline", "proposed", "risk", "guard"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError(f"innovation evidence field {key} must be a non-empty string")
    metrics = data.get("metrics")
    if not isinstance(metrics, dict) or not metrics:
        raise ValueError("innovation evidence metrics must be a non-empty object")
    return True


def register(workspace: Path, claim_id: str, value: str, unit: str, source: str, source_field: str,
             status="provisional", implementation=None, verifier=None, independence_report=None,
             paper_refs=None, note="", kind="headline", innovation_evidence=None):
    if not claim_id.strip() or not value.strip() or not source_field.strip():
        raise ValueError("claim_id, value and source_field are required")
    if status not in {"provisional", "verified"}:
        raise ValueError("status must be provisional or verified")
    if kind not in CLAIM_KINDS:
        raise ValueError(f"kind must be one of {sorted(CLAIM_KINDS)}")

    state = load(workspace)
    record = {
        "claim_id": claim_id,
        "kind": kind,
        "value": value,
        "unit": unit,
        "source": file_record(workspace, source),
        "source_field": source_field,
        "status": status,
        "paper_refs": list(paper_refs or []),
        "note": note,
        "recorded_at": now(),
    }
    if implementation:
        record["implementation"] = file_record(workspace, implementation)
    if verifier:
        record["verifier"] = file_record(workspace, verifier)
    if independence_report:
        ir = file_record(workspace, independence_report)
        report = _load_independence_report(workspace, ir)
        ir["reported_status"] = report.get("status")
        ir["verifier_sha256"] = report.get("verifier_sha256")
        ir["implementation_sha256"] = report.get("implementation_sha256")
        record["independence_report"] = ir
    if innovation_evidence:
        er = file_record(workspace, innovation_evidence)
        evidence = _load_json_record(workspace, er)
        _validate_innovation_evidence(evidence)
        er["evidence_fields"] = sorted(evidence.keys())
        record["innovation_evidence"] = er

    if status == "verified":
        if not verifier:
            raise ValueError("verified claims require a verifier artifact")
        if implementation:
            if not independence_report:
                raise ValueError("verified claims with an implementation require an independence report")
            _validate_independence_binding(
                _load_independence_report(workspace, record["independence_report"]),
                record["verifier"], record["implementation"],
            )
        if kind == "innovation":
            if not innovation_evidence:
                raise ValueError("verified innovation claims require --innovation-evidence")
            if not record["paper_refs"]:
                raise ValueError("verified innovation claims require at least one paper_ref")
            _validate_innovation_evidence(_load_json_record(workspace, record["innovation_evidence"]))

    prior = state["claims"].get(claim_id)
    if prior:
        state["history"].append({"claim_id": claim_id, "superseded_at": now(), "record": prior})
    state["claims"][claim_id] = record
    save(workspace, state)
    return record


def check(workspace: Path):
    state = load(workspace)
    issues = []
    for claim_id, claim in state.get("claims", {}).items():
        claim.setdefault("kind", "headline")
        for field in ("source", "implementation", "verifier", "independence_report", "innovation_evidence"):
            rec = claim.get(field)
            if not rec:
                continue
            try:
                p = safe_file(workspace, rec["path"])
            except ValueError as exc:
                issues.append({"severity": "error", "claim_id": claim_id, "code": "missing-evidence", "detail": str(exc)})
                continue
            current = sha256(p)
            if current != rec.get("sha256"):
                issues.append({"severity": "error", "claim_id": claim_id, "code": "evidence-drift",
                               "detail": f"{rec['path']} changed after claim registration"})

        if claim.get("status") == "verified":
            verifier = claim.get("verifier")
            implementation = claim.get("implementation")
            if not verifier:
                issues.append({"severity": "error", "claim_id": claim_id, "code": "verified-without-verifier"})
            if implementation:
                ir = claim.get("independence_report")
                if not ir:
                    issues.append({"severity": "error", "claim_id": claim_id, "code": "independence-not-passed"})
                else:
                    try:
                        report = _load_independence_report(workspace, ir)
                        _validate_independence_binding(report, verifier, implementation)
                    except (ValueError, KeyError, json.JSONDecodeError) as exc:
                        issues.append({"severity": "error", "claim_id": claim_id, "code": "independence-binding-invalid",
                                       "detail": str(exc)})
            if claim.get("kind") == "innovation":
                er = claim.get("innovation_evidence")
                if not er:
                    issues.append({"severity": "error", "claim_id": claim_id, "code": "innovation-evidence-missing"})
                else:
                    try:
                        _validate_innovation_evidence(_load_json_record(workspace, er))
                    except (ValueError, KeyError, json.JSONDecodeError) as exc:
                        issues.append({"severity": "error", "claim_id": claim_id, "code": "innovation-evidence-invalid",
                                       "detail": str(exc)})
                if not claim.get("paper_refs"):
                    issues.append({"severity": "error", "claim_id": claim_id, "code": "innovation-paper-ref-missing"})

    status = "failed" if any(i["severity"] == "error" for i in issues) else "passed"
    return {
        "status": status,
        "claims": len(state.get("claims", {})),
        "innovation_claims": sum(1 for c in state.get("claims", {}).values() if c.get("kind", "headline") == "innovation"),
        "issues": issues,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["add", "check", "get"])
    ap.add_argument("--workspace", type=Path, required=True)
    ap.add_argument("--claim-id")
    ap.add_argument("--kind", choices=sorted(CLAIM_KINDS), default="headline")
    ap.add_argument("--value")
    ap.add_argument("--unit", default="")
    ap.add_argument("--source")
    ap.add_argument("--source-field")
    ap.add_argument("--status", choices=["provisional", "verified"], default="provisional")
    ap.add_argument("--implementation")
    ap.add_argument("--verifier")
    ap.add_argument("--independence-report")
    ap.add_argument("--innovation-evidence")
    ap.add_argument("--paper-ref", action="append", default=[])
    ap.add_argument("--note", default="")
    ap.add_argument("--output", type=Path)
    a = ap.parse_args()
    try:
        if a.command == "add":
            if not all([a.claim_id, a.value, a.source, a.source_field]):
                raise ValueError("add requires --claim-id --value --source --source-field")
            result = register(
                a.workspace, a.claim_id, a.value, a.unit, a.source, a.source_field,
                a.status, a.implementation, a.verifier, a.independence_report,
                a.paper_ref, a.note, a.kind, a.innovation_evidence,
            )
        elif a.command == "get":
            if not a.claim_id:
                raise ValueError("get requires --claim-id")
            result = load(a.workspace).get("claims", {}).get(a.claim_id)
            if result is None:
                raise ValueError(f"Unknown claim: {a.claim_id}")
        else:
            result = check(a.workspace)
        rendered = json.dumps(result, ensure_ascii=False, indent=2)
        if a.output:
            a.output.parent.mkdir(parents=True, exist_ok=True)
            a.output.write_text(rendered, encoding="utf-8")
        print(rendered)
        if a.command == "check" and result["status"] == "failed":
            raise SystemExit(1)
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        ap.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
