import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / '.github/scripts/check_nonempty_pr.py'


def run(value):
    env = dict(os.environ)
    env.pop('PR_CHANGED_FILES', None)
    if value is not None:
        env['PR_CHANGED_FILES'] = value
    return subprocess.run([sys.executable, str(SCRIPT)], env=env, capture_output=True, text=True)


class NonEmptyPrTest(unittest.TestCase):
    def test_positive_counts_pass(self):
        for value in ('1', '5', '120'):
            with self.subTest(value=value):
                self.assertEqual(run(value).returncode, 0)

    def test_empty_and_invalid_counts_fail(self):
        for value in ('0', '', None, 'abc', '-1', '1.5'):
            with self.subTest(value=value):
                result = run(value)
                self.assertEqual(result.returncode, 1)
                self.assertIn('no changed files', result.stdout)

    def test_workflow_wires_the_check(self):
        workflow = (ROOT / '.github/workflows/pr-body-check.yml').read_text()
        self.assertIn('PR_CHANGED_FILES: ${{ github.event.pull_request.changed_files', workflow)
        self.assertIn('run: python .github/scripts/check_nonempty_pr.py', workflow)


if __name__ == '__main__':
    unittest.main()
