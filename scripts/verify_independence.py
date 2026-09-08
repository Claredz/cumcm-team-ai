#!/usr/bin/env python3
"""Structural guard against self-verification by importing or re-running the implementation under test."""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
from pathlib import Path


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _literal_refers_to_impl(value: str, impl_name: str, impl_stem: str) -> bool:
    """Catch path/module literals without flagging prose that merely mentions a solver."""
    raw = value.strip().replace("\\", "/")
    if raw in {impl_name, impl_stem}:
        return True
    tail = raw.rsplit("/", 1)[-1]
    return tail == impl_name or tail == impl_stem or tail == f"{impl_stem}.py"


def audit(verifier: Path, implementation: Path):
    issues = []
    vr = verifier.resolve()
    ir = implementation.resolve()
    if vr == ir:
        issues.append({"severity": "error", "code": "same-file", "detail": "Verifier and implementation are the same file"})
    if verifier.is_file() and implementation.is_file() and sha256(verifier) == sha256(implementation):
        issues.append({"severity": "error", "code": "same-content", "detail": "Verifier and implementation have identical SHA256"})

    text = verifier.read_text(encoding="utf-8", errors="replace")
    impl_stem = implementation.stem
    impl_name = implementation.name
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return {"status": "needs_review", "verifier": str(verifier), "implementation": str(implementation),
                "issues": [{"severity": "review", "code": "parse-failed", "detail": str(exc)}]}

    imported = set()
    string_literals = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            string_literals.append(node.value)

    suspicious_imports = sorted(name for name in imported if name.split(".")[-1] == impl_stem)
    if suspicious_imports:
        issues.append({"severity": "error", "code": "imports-implementation", "imports": suspicious_imports,
                       "detail": "Verifier directly imports the implementation under test"})

    suspicious_strings = sorted({s for s in string_literals if _literal_refers_to_impl(s, impl_name, impl_stem)})
    if suspicious_strings:
        issues.append({"severity": "error", "code": "references-implementation-path",
                       "detail": "Verifier contains a literal module/path reference to the implementation under test",
                       "literals": suspicious_strings[:10]})

    if any(i["severity"] == "error" for i in issues):
        status = "failed"
    elif issues:
        status = "needs_review"
    else:
        status = "passed"
    return {"status": status, "verifier": str(verifier), "implementation": str(implementation),
            "verifier_sha256": sha256(verifier), "implementation_sha256": sha256(implementation),
            "issues": issues,
            "note": "This is a structural independence guard only; mathematical/algorithmic independence still needs review."}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verifier", type=Path, required=True)
    ap.add_argument("--implementation", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    if not a.verifier.is_file() or not a.implementation.is_file():
        ap.error("verifier and implementation must be existing files")
    report = audit(a.verifier, a.implementation)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "issues": len(report["issues"]), "output": str(a.output)}))
    raise SystemExit(1 if report["status"] == "failed" else 0)


if __name__ == "__main__":
    main()
