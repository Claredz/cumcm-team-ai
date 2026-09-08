import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_layout_module():
    path = ROOT / "scripts" / "check_layout.py"
    spec = importlib.util.spec_from_file_location("check_layout", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ModelingFirstIntegrationTests(unittest.TestCase):
    def test_modeling_constitution_precedes_workflow_in_root_skill(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertLess(text.index("## 建模宪法"), text.index("## 启动与恢复"))
        self.assertIn("DAG 是执行器", text)

    def test_stage3_reads_production_modeling_before_catalog(self):
        text = (ROOT / "references" / "stage_03_model_selection.md").read_text(encoding="utf-8")
        self.assertLess(text.index("references/production/modeling.md"), text.index("references/model_catalog.md"))
        self.assertIn("模型目录是工具书，不是路由器", text)

    def test_production_coding_does_not_require_personal_absolute_paths(self):
        text = (ROOT / "references" / "production" / "coding.md").read_text(encoding="utf-8")
        self.assertNotIn("必须用**绝对路径**", text)
        self.assertNotIn("/abs/path/", text)
        self.assertIn("workspace-relative", text)
        self.assertIn("不得把", text)

    def test_architecture_compatibility_paths_exist(self):
        expected = [
            ROOT / "references" / "architecture-diagram.md",
            ROOT / "skills" / "tikz-architecture-diagram" / "SKILL.md",
            ROOT / "skills" / "tikz-architecture-diagram" / "scripts" / "check_overlap.py",
            ROOT / "skills" / "tikz-architecture-diagram" / "templates" / "fig.tex",
            ROOT / "templates" / "diagrams" / "architecture.tex",
            ROOT / "templates" / "diagrams" / "flow_snake.tex",
        ]
        self.assertTrue(all(path.is_file() for path in expected))

    def test_horizontal_snake_override_is_explicit(self):
        policy = (ROOT / "references" / "integration-policy.md").read_text(encoding="utf-8")
        self.assertIn("蛇形横向", policy)
        self.assertIn("“纵向 TikZ”", policy)

    def test_layout_heuristics_are_advisory(self):
        layout = load_layout_module()
        hint = layout.classify_caption_length(50)
        self.assertEqual(hint["severity"], "hint")
        self.assertEqual(layout.exit_code({"status": "advisory"}), 0)
        self.assertEqual(layout.exit_code({"status": "needs_review"}), 0)
        self.assertEqual(layout.exit_code({"status": "needs_review"}, strict_review=True), 1)
        self.assertEqual(layout.exit_code({"status": "failed"}), 1)

    def test_modeling_constitution_explicitly_demotes_catalog(self):
        text = (ROOT / "references" / "modeling-constitution.md").read_text(encoding="utf-8")
        self.assertIn("模型目录只是工具书", text)
        self.assertIn("复杂度必须挣得资格", text)
        self.assertIn("允许 0 个创新点", text)


if __name__ == "__main__":
    unittest.main()
