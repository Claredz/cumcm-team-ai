#!/usr/bin/env python3
"""Aggregate workflow, provenance, citation, PDF and compliance checks into one READY/BLOCKED verdict."""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
import claim_registry  # noqa: E402
import workflow  # noqa: E402


def now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_workspace_file(workspace: Path, raw: str):
    p = Path(raw)
    if not p.is_absolute():
        p = workspace / p
    p = p.resolve()
    root = workspace.resolve()
    if not p.is_relative_to(root) or not p.is_file() or p.stat().st_size == 0:
        raise ValueError(f"Missing/empty/outside-workspace file: {raw}")
    return p


def input_record(workspace: Path, rel: str):
    p = resolve_workspace_file(workspace, rel)
    return {"path": str(p.relative_to(workspace.resolve())), "sha256": sha256(p)}


def read_json(workspace: Path, rel: str):
    rec = input_record(workspace, rel)
    data = json.loads((workspace / rec["path"]).read_text(encoding="utf-8"))
    return data, rec


def bind_reported_file(workspace: Path, inputs: dict, issues: list, label: str,
                       raw_path: str | None, expected_sha: str | None, code: str):
    if not raw_path or not expected_sha:
        issues.append({"severity": "error", "code": f"{code}-binding-missing",
                       "detail": f"Audit report lacks path/hash binding for {label}"})
        return
    try:
        p = resolve_workspace_file(workspace, raw_path)
    except ValueError as exc:
        issues.append({"severity": "error", "code": f"{code}-target-missing", "detail": str(exc)})
        return
    current = sha256(p)
    inputs[label] = {"path": str(p.relative_to(workspace.resolve())), "sha256": current}
    if current != expected_sha:
        issues.append({"severity": "error", "code": f"{code}-target-drift",
                       "detail": f"{inputs[label]['path']} changed after its audit"})


def build_gate(workspace: Path, citation_rel="state/citation-audit.json",
               pdf_rel="state/pdf-audit-final.json"):
    issues = []
    inputs = {}

    state_path = workspace / "state/decision_log.json"
    if not state_path.is_file():
        raise ValueError("No state/decision_log.json; initialize workflow first")
    inputs["decision_log"] = input_record(workspace, "state/decision_log.json")

    rec = workflow.reconcile(workspace)
    for warning in rec["reconcile"]["warnings"]:
        issues.append({"severity": "error", "code": f"workflow-{warning['code']}", "detail": warning["detail"]})
    if rec.get("stage") != 9:
        issues.append({"severity": "error", "code": "workflow-not-at-review-stage",
                       "detail": f"Final gate must run at Stage 9; current stage={rec.get('stage')}"})
    dag_path = workspace / "state/task_dag.json"
    if dag_path.is_file():
        inputs["task_dag"] = input_record(workspace, "state/task_dag.json")

    claims_path = workspace / "state/claims.json"
    if not claims_path.is_file():
        issues.append({"severity": "error", "code": "claims-missing", "detail": "state/claims.json is required for final headline-value provenance"})
    else:
        inputs["claims"] = input_record(workspace, "state/claims.json")
        claims_state = claim_registry.load(workspace)
        if not claims_state.get("claims"):
            issues.append({"severity": "error", "code": "claims-empty", "detail": "No active headline claims are registered"})
        provisional = sorted(k for k, v in claims_state.get("claims", {}).items() if v.get("status") != "verified")
        if provisional:
            issues.append({"severity": "error", "code": "claims-unverified", "claims": provisional})
        checked = claim_registry.check(workspace)
        for issue in checked["issues"]:
            issues.append({"severity": "error", "code": f"claim-{issue.get('code')}", "detail": issue.get("detail", ""),
                           "claim_id": issue.get("claim_id")})

    try:
        citation, inputs["citation_audit"] = read_json(workspace, citation_rel)
        if citation.get("status") != "passed":
            issues.append({"severity": "error", "code": "citation-not-passed",
                           "detail": f"{citation_rel} status={citation.get('status')}"})
        citation_files = citation.get("file_sha256")
        if not isinstance(citation_files, list) or not citation_files:
            issues.append({"severity": "error", "code": "citation-binding-missing",
                           "detail": "Citation audit does not bind the paper sources to SHA256"})
        else:
            for idx, item in enumerate(citation_files):
                bind_reported_file(workspace, inputs, issues, f"citation_source_{idx}",
                                   item.get("path") if isinstance(item, dict) else None,
                                   item.get("sha256") if isinstance(item, dict) else None,
                                   "citation")
        if citation.get("bibliography"):
            bind_reported_file(workspace, inputs, issues, "citation_bibliography",
                               citation.get("bibliography"), citation.get("bibliography_sha256"), "citation")
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        issues.append({"severity": "error", "code": "citation-audit-missing", "detail": str(exc)})

    try:
        pdf, inputs["pdf_audit"] = read_json(workspace, pdf_rel)
        if pdf.get("status") != "passed":
            issues.append({"severity": "error", "code": "pdf-not-passed",
                           "detail": f"{pdf_rel} status={pdf.get('status')}"})
        bind_reported_file(workspace, inputs, issues, "final_pdf",
                           pdf.get("pdf"), pdf.get("pdf_sha256"), "pdf")
        tex_log = pdf.get("tex_log")
        if isinstance(tex_log, dict):
            bind_reported_file(workspace, inputs, issues, "final_tex_log",
                               tex_log.get("path"), tex_log.get("sha256"), "pdf-log")
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        issues.append({"severity": "error", "code": "pdf-audit-missing", "detail": str(exc)})

    state = workflow.load(workspace)
    checks = state.get("stages", {}).get("9", {}).get("compliance_checks", {})
    missing_checks = sorted(k for k, v in checks.items() if v is not True)
    if missing_checks:
        issues.append({"severity": "error", "code": "compliance-incomplete", "checks": missing_checks})
    if state.get("compliance", {}).get("ai_usage") is None:
        issues.append({"severity": "error", "code": "ai-ledger-unconfirmed",
                       "detail": "compliance.ai_usage is null/missing"})

    status = "BLOCKED" if issues else "READY"
    return {"status": status, "generated_at": now(), "inputs": inputs, "issues": issues,
            "summary": {"workflow_ready": rec["reconcile"]["ready"],
                        "active_claims": len(claim_registry.load(workspace).get("claims", {})) if claims_path.is_file() else 0,
                        "compliance_checks": checks}}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workspace", type=Path, required=True)
    ap.add_argument("--citation-report", default="state/citation-audit.json")
    ap.add_argument("--pdf-report", default="state/pdf-audit-final.json")
    ap.add_argument("--output", default="state/final-gate.json")
    a = ap.parse_args()
    try:
        report = build_gate(a.workspace, a.citation_report, a.pdf_report)
        output = (a.workspace / a.output).resolve()
        if not output.is_relative_to(a.workspace.resolve()):
            raise ValueError("output must stay inside workspace")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"status": report["status"], "issues": len(report["issues"]), "output": str(output)}))
        raise SystemExit(1 if report["status"] == "BLOCKED" else 0)
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        ap.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()