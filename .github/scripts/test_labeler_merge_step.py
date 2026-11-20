"""Run the inline 'merge plugin-local labels' script from labeler.yml with GITHUB_OUTPUT set, as CI does."""
import os, pathlib, re, subprocess, sys, tempfile, textwrap, unittest
import yaml

WORKFLOW = pathlib.Path(os.environ.get("LABELER_WORKFLOW") or (pathlib.Path(__file__).resolve().parents[1] / "workflows" / "labeler.yml"))

def script():
    wf = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    for step in wf["jobs"]["label"]["steps"]:
        if step.get("name") == "merge plugin-local labels":
            m = re.search(r"python - <<'PY'\n(.*?)\n\s*PY\s*$", step["run"], re.S)
            return textwrap.dedent(m.group(1))
    raise AssertionError("merge step not found")

class MergeStep(unittest.TestCase):
    def run_step(self, with_output=True, with_plugin_labels=True):
        with tempfile.TemporaryDirectory() as d:
            (pathlib.Path(d) / ".github").mkdir()
            (pathlib.Path(d) / ".github" / "labeler.yml").write_text("repo-label:\n- changed-files:\n  - any-glob-to-any-file: ['docs/**']\n")
            plug = pathlib.Path(d) / "plugins" / "p" / ".github"
            plug.mkdir(parents=True)
            if with_plugin_labels:
                (plug / "labels.yml").write_text("p-label:\n- changed-files:\n  - any-glob-to-any-file: ['src/**']\n")
            env = {k: v for k, v in os.environ.items() if k != "GITHUB_OUTPUT"}
            out = pathlib.Path(d) / "gh_output"
            if with_output:
                env["GITHUB_OUTPUT"] = str(out)
            r = subprocess.run([sys.executable, "-c", script()], cwd=d, env=env, capture_output=True, text=True, timeout=60, check=False)
            self.assertEqual(r.returncode, 0, r.stderr)
            merged_path = pathlib.Path(d) / "merged_labeler.yml"
            self.assertTrue(merged_path.is_file(), r.stdout + r.stderr)
            merged = merged_path.read_text(encoding="utf-8")
            if with_output:
                self.assertTrue(out.is_file(), r.stdout + r.stderr)
                return r, out.read_text(encoding="utf-8"), merged
            return r, "", merged

    def test_with_github_output_writes_outputs_and_merged_file(self):
        r, out, merged = self.run_step(True)
        self.assertIn("merged_labeler_path=merged_labeler.yml", out)
        self.assertIn("labels_count=2", out)
        parsed = yaml.safe_load(merged)
        self.assertIn("p-label", parsed)
        self.assertIn("repo-label", parsed)
        self.assertEqual(parsed["p-label"][0]["changed-files"][0]["any-glob-to-any-file"], ["plugins/p/src/**"])
        self.assertEqual(parsed["repo-label"][0]["changed-files"][0]["any-glob-to-any-file"], ["docs/**"])

    def test_without_github_output_still_runs(self):
        r, _, merged = self.run_step(False)
        self.assertIn("merged_labeler_path=merged_labeler.yml", r.stdout)
        self.assertIn("labels_count=2", r.stdout)
        self.assertEqual(set(yaml.safe_load(merged)), {"p-label", "repo-label"})

    def test_without_plugin_local_labels_keeps_repository_labels(self):
        r, out, merged = self.run_step(True, with_plugin_labels=False)
        self.assertIn("merged_labeler_path=merged_labeler.yml", out)
        self.assertIn("labels_count=1", out)
        parsed = yaml.safe_load(merged)
        self.assertEqual(set(parsed), {"repo-label"})
        self.assertEqual(parsed["repo-label"][0]["changed-files"][0]["any-glob-to-any-file"], ["docs/**"])

if __name__ == "__main__":
    unittest.main()
