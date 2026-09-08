# Maintainer instructions

This repository is the cumcm-team-ai skill product. Editing it does not start a contest workflow. Keep installation project-local by default.

SKILL.md and references/integration-policy.md govern runtime behavior. Preserve upstream notices in licenses/; update THIRD_PARTY_NOTICES.md when adding sources. Do not redistribute linked paper texts without clear permission.

Before publishing, run `python -m unittest discover -s tests -v`, `python -m compileall -q scripts templates/shared/code_starter`, all three `python scripts/doctor.py --competition <comp> --skip-tools` checks, and `git diff --check`. Report unexecuted checks. New deterministic helpers need meaningful success and failure cases.

Cross-platform support is part of the product contract: pull requests that change runtime scripts, paths, subprocess calls, setup docs, or workflow state must pass the GitHub Actions matrix on both `ubuntu-latest` and `windows-latest`. Core runtime commands must not require Bash-only tools; Bash/PowerShell-specific examples must be labeled and have a portable Python path or an equivalent command when they are part of the documented execution path.
