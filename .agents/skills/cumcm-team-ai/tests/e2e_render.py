#!/usr/bin/env python3
"""Generate a tiny synthetic regression example for real multi-contest rendering.

Not a past contest paper, not a competition solution, and not empirical corpus data.
"""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import workflow
import parse_problem


def make(workspace, competition):
    workflow.init(workspace, competition, 2027 if competition == "mcm" else 2026)
    x = np.arange(1, 6, dtype=float)
    y = 2*x + 1
    slope, intercept = np.linalg.lstsq(np.column_stack([x, np.ones_like(x)]), y, rcond=None)[0]
    assert np.allclose([slope, intercept], [2, 1])
    np.savetxt(workspace / "data/raw/synthetic.csv", np.column_stack([x, y]), delimiter=",", header="x,y", comments="")
    metrics = {"source": "synthetic known-answer fixture", "slope": float(slope), "intercept": float(intercept)}
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.scatter(x, y, label="Synthetic observations")
    ax.plot(x, slope*x+intercept, label="Least squares")
    ax.set(xlabel="x", ylabel="y")
    ax.legend()
    fig.tight_layout()
    fig.savefig(workspace / "figures/regression.png", dpi=150)
    plt.close(fig)
    (workspace / "results/metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
    problem = workspace / "problem/problem.md"
    problem.write_text("# Synthetic test, not a contest problem\nQuestion 1: Fit linear regression.\nQuestion 2: Evaluate residuals.\n", encoding="utf-8")
    package = parse_problem.parse(problem, [workspace / "data/raw/synthetic.csv"])
    workflow.save(workspace / "state/problem-package.json", package)
    state = workflow.load(workspace)
    state["paper_metadata"].update(title="合成回归编译测试" if competition != "mcm" else "Synthetic regression compilation test", keywords=["regression", "synthetic"], problem="A", mcm_control_number="2700001", diangong_registration_number="123456")
    state["compliance"]["ai_usage"] = [{"tool": "Codex", "model": "not independently observed in fixture", "version": "test fixture", "use_stage": "test generation", "purpose": "Generate toolchain test material", "paper_sections": ["test"], "disclosure": "This is synthetic test metadata, not a real contest use record.", "human_review": "Not a real participant sign-off; automated fixture validation only."}]
    workflow.save(workspace / "state/decision_log.json", state)
    english = competition == "mcm"
    sections = {
        "01_abstract.md": "This synthetic fixture fits five points from $y=2x+1$. The fitted slope is 2 and intercept is 1. It tests the toolchain, not a contest claim." if english else "本样稿使用五个合成样本检验工具链。已知关系为 $y=2x+1$，最小二乘求得斜率为 2、截距为 1。本样稿不是往届论文或参赛作品。",
        "02_problem_restate.md": "# Problem\n\nFit the known-answer synthetic sample.",
        "03_analysis.md": "# Analysis\n\nUse least squares and independently compare with the generating equation.",
        "04_assumptions.md": "# Assumptions\n\nThe synthetic data have no observation noise. This is not assumed for real data.",
        "05_notation.md": "# Notation\n\n$x$ denotes the input and $y$ the generated response.",
        "06_models.md": f"# Model\n\n$$\\min_{{a,b}} \\sum_i (y_i-a x_i-b)^2$$\n\nComputed slope: {slope:.8f}; intercept: {intercept:.8f}.\n\n![Synthetic sample and fitted line](figures/regression.png)\n",
        "07_sensitivity.md": "# Verification\n\nThe fitted parameters agree with the generating equation within absolute tolerance $10^{-10}$. The fixture does not estimate population uncertainty.",
        "08_evaluation.md": "# Limitations\n\nThis exact synthetic relation only exercises the implementation and cannot support claims about real-world predictive performance.",
        "09_references.md": "# References\n\nNo external scientific claims are made in this synthetic fixture." if english else "# 参考文献\n\n本测试未引用外部科学结论。",
        "10_appendix.md": "# Appendix\n\nInput and computed values are in synthetic.csv and metrics.json. This test draft is not a complete submission package." if english else "# 附录\n\n输入与结果见 synthetic.csv 和 metrics.json。本测试稿不是正式参赛材料。",
    }
    for filename, body in sections.items():
        (workspace / "paper_workspace" / filename).write_text(body + "\n", encoding="utf-8")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--competition", choices=["cumcm", "mcm", "diangong"], default="cumcm")
    args = parser.parse_args()
    if (args.workspace / "state/decision_log.json").exists():
        parser.error("Choose a new test workspace; this generator does not overwrite existing work")
    print(json.dumps(make(args.workspace, args.competition)))
