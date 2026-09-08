---
stage: 8
name: writing
duration_h: 12-30
inputs: ["decision_log.stages.0-7", "decision_log.competition", "decision_log.task_type", "state/claims.json"]
outputs:
  - "stage.8.{section_word_counts, figures_per_subproblem, tables_per_subproblem, abstract_drafts, innovation_claims_used, ai_use_log, compliance}"
  - "paper_workspace/*.md"
  - "paper.tex"
loads_reference:
  - "references/structural-innovation.md"
  - "competitions/<competition>/current_rules.md"
  - "competitions/<competition>/winning_patterns.md"
  - "competitions/<competition>/phrase_bank.md"
  - "competitions/<competition>/empirical.json"
loads_template:
  - "competitions/<competition>/paper_skeleton.md"
  - "competitions/<competition>/abstract_template.md"
  - "templates/latex/<competition>/"
feedback: ["L1", "L2_at_end"]
next: stage_09_review
---

# Stage 8 — Assemble the paper

> v2 适配：本页为导入参考。执行前以根 SKILL.md 和 references/integration-policy.md 为准。Turn the validated Stage 0–7 outputs into one coherent paper. Do not invent new results while writing.

## 1. Lock the current rules first

1. Read `competitions/<competition>/current_rules.md` when present.
2. Open the linked official rules and confirm they are still current for the contest year.
3. Record verification date, source URL, page/font/file-size limits, anonymity and AI-disclosure requirements.
4. Repository baseline conflicts with official source时，以官方来源为准并记录 mismatch。

Empirical distributions、winning patterns 和 rubric 都不是官方规则。

## 2. Load only the active competition pack

Read `paper_skeleton.md`、`abstract_template.md`、`winning_patterns.md`、`phrase_bank.md`、`empirical.json` from the active competition only. Empirical observations are writing aids, not award thresholds.

## 3. Stable paper workspace

Create under `<cwd>/paper_workspace/`:

| File | Content |
|---|---|
| `01_abstract.md` | Abstract/Summary Sheet, written last |
| `02_problem_restate.md` | Problem context and restatement |
| `03_analysis.md` | Decomposition and technical route |
| `04_assumptions.md` | Supported assumptions |
| `05_notation.md` | Symbols and units |
| `06_models.md` | Models, algorithms, results and interpretation |
| `07_sensitivity.md` | Robustness, failure regions and innovation stress tests |
| `08_evaluation.md` | Strengths, limitations and transfer conditions |
| `09_references.md` | Verified references |
| `10_appendix.md` | Essential code/support manifest |
| `11_ai_use_report.md` | MCM only |

Write body first, abstract last. Every number in abstract must already exist in the body and in the claim/evidence chain.

## 4. Keep one evidence chain

For every subproblem preserve:

`question → assumptions → formulation → solver → result → validation → interpretation`

Before moving on verify symbols、chosen formulation、stored result values、figures、citations and limitations all agree with earlier stages.

## 5. Innovation claims are a separate evidence class

Read `references/structural-innovation.md` and `state/claims.json` before writing any “创新、改进、提高效率、显著提升、结构化求解”等表述。

Only a **verified innovation claim** may be presented as an innovation. Candidate/tested/adopted-but-unverified/rejected ideas may only appear as limitations、尝试或未来工作，不得写成成果。

Every innovation paragraph must answer in order:

`原方法困难 → 结构观察 → 改变 → 为什么有效 → baseline → 量化对比 → 风险/适用边界`

A valid innovation claim must point to evidence registered by `claim_registry.py` and include a paper reference/section path. Example narrative:

> 直接全域高精度搜索计算量过高。利用近似机理保留主导几何结构，先定位候选区，再在扩张后的局部区域精细求解。与相同输入下的 full-domain baseline 相比，运行时间从 X 降至 Y，目标值差异为 Z；随机全域抽查未发现被裁掉的更优区域。该收益只在已测试参数域内成立。

Do not use model name novelty as innovation evidence. `A+B+C` only counts when the interface explains which component solves which explicit difficulty and the comparison verifies the gain.

Record in Stage 8:

```json
{
  "innovation_claims_used": [
    {"claim_id": "innovation.q3.coarse_to_fine", "paper_ref": "paper_workspace/06_models.md#..."}
  ]
}
```

If the paper needs an innovation statement that is not yet verified/registered, return to Stage 5/6 rather than inventing prose.

## 6. Apply the competition branch

Use the current official competition rules and renderer. CUMCM、MCM/ICM、电工杯的 page limits、AI disclosure、cover/summary structure are not interchangeable. Problem-specific deliverables count according to current official rules.

## 7. Maintain the AI-use ledger

Keep `decision_log.compliance.ai_usage` current with tool/provider/model、date、purpose、key prompt/response or paths、adopted content、human changes and verification. Do not store credentials.

## 8. Render without detached sections

From the project root:

```bash
python <skill>/scripts/render_paper.py \
  --competition <competition> \
  --workspace paper_workspace/ \
  --output-dir paper_output/
```

A PDF with missing section inputs is a failure even if LaTeX exits successfully.

## 9. Score using active overlay

Use Stage 8 dimensions from the selected competition overlay. Do not reuse one competition's abstract/rubric conventions for another.

## Exit conditions

- all required sections/deliverables exist;
- paper agrees with Stage 0–7 and stored results;
- official rules rechecked and recorded;
- AI uses and citations logged;
- every explicit innovation claim is `verified`, registered, traceable to baseline/proposed evidence, and has a paper reference;
- no rejected/unverified opportunity is written as achieved innovation;
- renderer includes every section;
- L1 passes and final L2 has no unresolved high-severity conflict.

Then enter `stage_09_review.md`.
