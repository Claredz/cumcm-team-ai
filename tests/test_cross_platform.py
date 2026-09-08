from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class CrossPlatformDocsTests(unittest.TestCase):
    def test_ci_runs_windows_and_ubuntu(self):
        text = (ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")
        self.assertIn("ubuntu-latest", text)
        self.assertIn("windows-latest", text)
        self.assertIn("matrix:", text)
        self.assertIn("fail-fast: false", text)

    def test_setup_guides_exist_for_both_platform_families(self):
        win = (ROOT / "references" / "setup-windows.md").read_text(encoding="utf-8")
        linux = (ROOT / "references" / "setup-linux-wsl.md").read_text(encoding="utf-8")
        self.assertIn("PowerShell", win)
        self.assertIn("New-Item", win)
        self.assertIn("Select-String", win)
        self.assertIn("WSL2", linux)
        self.assertIn("~/cumcm", linux)

    def test_readme_declares_both_supported_paths(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Windows 10/11 + PowerShell", text)
        self.assertIn("Linux", text)
        self.assertIn("WSL2", text)
        self.assertIn("setup-windows.md", text)
        self.assertIn("setup-linux-wsl.md", text)

    def test_toolchain_core_commands_do_not_require_bash_continuations(self):
        text = (ROOT / "references" / "toolchain.md").read_text(encoding="utf-8")
        legacy_multiline = "main.pdf --competition cumcm " + chr(92) + "\n"
        self.assertNotIn(legacy_multiline, text)
        self.assertIn("Windows PowerShell", text)
        self.assertIn("Linux/WSL2", text)


class DoctorPlatformTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doctor = load_module(ROOT / "scripts" / "doctor.py", "doctor_cross_platform")

    def test_windows_is_supported(self):
        with mock.patch.object(self.doctor.platform, "system", return_value="Windows"), mock.patch.object(
            self.doctor.platform, "release", return_value="11"
        ):
            checks = self.doctor.run_checks("cumcm", check_tools=False)
        platform_check = next(item for item in checks if item.name == "platform")
        self.assertEqual(platform_check.status, "pass")
        self.assertIn("Windows", platform_check.detail)

    def test_wsl_is_detected_as_supported_linux(self):
        with mock.patch.dict(self.doctor.os.environ, {"WSL_DISTRO_NAME": "Ubuntu"}, clear=False), mock.patch.object(
            self.doctor.platform, "system", return_value="Linux"
        ), mock.patch.object(self.doctor.platform, "release", return_value="6.6.87.2-microsoft-standard-WSL2"):
            checks = self.doctor.run_checks("cumcm", check_tools=False)
        platform_check = next(item for item in checks if item.name == "platform")
        self.assertEqual(platform_check.status, "pass")
        self.assertIn("WSL/Linux", platform_check.detail)

    def test_human_output_uses_ascii_status_labels(self):
        checks = [self.doctor.Check(name="x", status="pass", detail="ok")]
        labels = {"pass": "[OK]", "warn": "[WARN]", "fail": "[FAIL]"}
        self.assertEqual(labels[checks[0].status], "[OK]")


if __name__ == "__main__":
    unittest.main()
