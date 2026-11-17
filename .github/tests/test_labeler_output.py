"""Execute the actual labeler workflow shell step, without GitHub API access."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/labeler.yml"


class LabelerOutputTest(unittest.TestCase):
    def run_step(self, output_mode):
        workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        step = next(s for s in workflow["jobs"]["label"]["steps"]
                    if s.get("name") == "merge plugin-local labels")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".github").mkdir()
            (root / ".github/labeler.yml").write_text("ci: []\n", encoding="utf-8")
            plugin = root / "plugins/example/.github"
            plugin.mkdir(parents=True)
            (plugin / "labels.yml").write_text(
                "tests:\n  - changed-files:\n      - any-glob-to-any-file: 'tests/**'\n",
                encoding="utf-8")
            output = root / "github-output"
            output.write_text("previous=value\n", encoding="utf-8")
            env = os.environ.copy()
            env.pop("GITHUB_OUTPUT", None)
            if output_mode == "file":
                env["GITHUB_OUTPUT"] = str(output)
            elif output_mode == "empty":
                env["GITHUB_OUTPUT"] = ""
            result = subprocess.run(["bash", "-e", "-c", step["run"]],
                                    cwd=root, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            expected = "merged_labeler_path=merged_labeler.yml\nlabels_count=2\n"
            if output_mode == "file":
                self.assertEqual(output.read_text(encoding="utf-8"), "previous=value\n" + expected)
                self.assertEqual(result.stdout, "")
            else:
                self.assertEqual(result.stdout, expected)
                self.assertEqual(output.read_text(encoding="utf-8"), "previous=value\n")
            merged = yaml.safe_load((root / "merged_labeler.yml").read_text(encoding="utf-8"))
            self.assertEqual(set(merged), {"ci", "tests"})
            self.assertEqual(merged["tests"][0]["changed-files"][0]["any-glob-to-any-file"],
                             ["plugins/example/tests/**"])

    def test_github_output_appends_both_outputs(self):
        self.run_step("file")

    def test_missing_github_output_uses_stdout(self):
        self.run_step("missing")

    def test_empty_github_output_uses_stdout(self):
        self.run_step("empty")

class LabelerDuplicateKeyTest(unittest.TestCase):
    def run_merge(self, repo_config, plugin_files):
        workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        step = next(s for s in workflow["jobs"]["label"]["steps"]
                    if s.get("name") == "merge plugin-local labels")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".github").mkdir()
            (root / ".github/labeler.yml").write_text(repo_config, encoding="utf-8")
            for rel, content in plugin_files.items():
                target = root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            env = os.environ.copy()
            env.pop("GITHUB_OUTPUT", None)
            result = subprocess.run(["bash", "-e", "-c", step["run"]],
                                    cwd=root, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            merged = yaml.safe_load((root / "merged_labeler.yml").read_text(encoding="utf-8"))
            return merged, result.stderr

    def test_same_key_across_plugins_unions_globs(self):
        merged, err = self.run_merge(
            "ci: []\n",
            {
                "plugins/nebula/.github/labels.yml":
                    "plugin-docs:\n  - changed-files:\n      - any-glob-to-any-file: 'docs/**'\n",
                "plugins/aero/.github/labels.yml":
                    "plugin-docs:\n  - changed-files:\n      - any-glob-to-any-file: 'docs/**'\n"
                    "e2e:\n  - changed-files:\n      - any-glob-to-any-file: 'e2e/**'\n",
            })
        globs = merged["plugin-docs"][0]["changed-files"][0]["any-glob-to-any-file"]
        self.assertEqual(globs, ["plugins/aero/docs/**", "plugins/nebula/docs/**"])
        self.assertEqual(merged["e2e"][0]["changed-files"][0]["any-glob-to-any-file"],
                         ["plugins/aero/e2e/**"])
        self.assertEqual(merged["ci"], [])
        self.assertNotIn("conflicts", err)

    def test_repo_label_still_wins_over_plugin_key(self):
        merged, err = self.run_merge(
            "documentation:\n  - changed-files:\n      - any-glob-to-any-file: 'README.md'\n",
            {
                "plugins/aero/.github/labels.yml":
                    "documentation:\n  - changed-files:\n      - any-glob-to-any-file: 'docs/**'\n",
            })
        self.assertEqual(merged["documentation"][0]["changed-files"][0]["any-glob-to-any-file"],
                         "README.md")
        self.assertIn("conflicts with a repo label", err)

    def test_duplicate_globs_are_not_duplicated(self):
        merged, err = self.run_merge(
            "ci: []\n",
            {
                "plugins/a/.github/labels.yml":
                    "tests:\n  - changed-files:\n      - any-glob-to-any-file:\n          - 'tests/**'\n          - 'extra/**'\n",
                "plugins/b/.github/labels.yml":
                    "tests:\n  - changed-files:\n      - any-glob-to-any-file: 'tests/**'\n",
            })
        globs = merged["tests"][0]["changed-files"][0]["any-glob-to-any-file"]
        self.assertEqual(globs, ["plugins/a/tests/**", "plugins/a/extra/**", "plugins/b/tests/**"])


if __name__ == "__main__":
    unittest.main()
