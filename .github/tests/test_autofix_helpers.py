import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(name):
    path = ROOT / '.github/scripts' / (name + '.py')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ELIGIBILITY = load('autofix_eligibility')
TASK = load('autofix_task')


def pr(**changes):
    value = {
        'state': 'open', 'draft': False, 'changed_files': 3,
        'head': {'ref': 'fix', 'repo': {'id': 42}},
        'base': {'ref': 'main'},
    }
    value.update(changes)
    return value


class EligibilityTest(unittest.TestCase):
    def test_eligible(self):
        self.assertIsNone(ELIGIBILITY.eligible(pr(), 42))

    def test_refusals(self):
        cases = [
            (pr(state='closed'), 'pr_not_open'),
            (pr(draft=True), 'draft_pr'),
            (pr(draft='no'), 'malformed_draft'),
            (pr(head={'ref': 'x', 'repo': {'id': 99}}), 'fork_head_outside_scope'),
            (pr(base={'ref': 'dev'}), 'wrong_base'),
            (pr(changed_files=0), 'empty_pr'),
            (pr(changed_files='3'), 'empty_pr'),
        ]
        for value, reason in cases:
            with self.subTest(reason=reason):
                self.assertEqual(ELIGIBILITY.eligible(value, 42), reason)


class TaskTest(unittest.TestCase):
    def test_strips_comments_and_caps_body(self):
        comments = [
            {'path': 'a.py', 'line': 7, 'body': '<!-- hidden --> real finding'},
            {'path': 'b.py', 'body': 'x' * 5000},
        ]
        out = TASK.build(comments, limit=100)
        self.assertIn('a.py:7 - real finding', out)
        self.assertNotIn('hidden', out)
        self.assertLessEqual(len(out.split('b.py:? - ')[1]), 101)

    def test_cli_is_shell_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'comments.json'
            path.write_text(json.dumps([{'path': 'a.py', 'body': '$(exit 9)'}]))
            result = subprocess.run([sys.executable, str(ROOT / '.github/scripts/autofix_task.py'), str(path)],
                                    capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('$(exit 9)', result.stdout)

    def test_workflow_is_disabled_by_default(self):
        workflow = (ROOT / '.github/workflows/auto-fix.yml').read_text()
        self.assertIn("vars.AUTOFIX_ENABLED == 'true'", workflow)
        self.assertNotIn('pull_request_target:', workflow)
        self.assertIn('autofix_eligibility.py', workflow)


if __name__ == '__main__':
    unittest.main()
