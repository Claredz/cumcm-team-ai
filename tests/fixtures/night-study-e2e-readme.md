# Night-study-space regression fixture

This fixture distills the failure modes observed in the 2026-09-08 synthetic night shared-study-space dry run. It intentionally does **not** preserve the original modeling answer; it preserves the workflow failures that the skill must catch mechanically.

Covered failure classes:

- final PDF exists while `decision_log.json` is still at Stage 0;
- Stage 3 cannot advance while a gated DAG task is unfinished;
- ten references with zero body citations fail citation audit;
- a 39.5 pt `Overfull \\hbox` fails PDF audit;
- a verifier importing the implementation fails the structural independence gate;
- a verified headline claim is SHA-bound to source and verification evidence;
- `final_gate.py` produces one `READY/BLOCKED` verdict;
- changing a frozen result after finalization invalidates provenance and the stale final gate.

The fixture is synthetic and contains no competition answer key.
