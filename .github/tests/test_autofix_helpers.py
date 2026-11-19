import importlib.util
import json
import subprocess
import sys
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


def threads(nodes):
    return {'data': {'repository': {'pullRequest': {'reviewThreads': {'nodes': nodes}}}}}


def thread(body, *, resolved=False, outdated=False, path='a.py'):
    return {
        'isResolved': resolved, 'isOutdated': outdated,
        'comments': {'nodes': [{'path': path, 'line': 7, 'body': body}]},
    }


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

    def test_cli_rejects_non_ascii_digits(self):
        result = subprocess.run([sys.executable, str(ROOT / '.github/scripts/autofix_eligibility.py'), '٤٢'],
                                input='{}', capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)


class TaskTest(unittest.TestCase):
    def test_skips_resolved_and_outdated_threads(self):
        data = threads([
            thread('stale finding', resolved=True),
            thread('outdated finding', outdated=True),
            thread('current finding'),
        ])
        out = TASK.build(data)
        self.assertIn('current finding', out)
        self.assertNotIn('stale finding', out)
        self.assertNotIn('outdated finding', out)

    def test_redacts_secrets_and_caps_size(self):
        data = threads([thread('token ghp_' + 'a' * 40 + ' here'), thread('x' * 5000)])
        out = TASK.build(data, limit=100)
        self.assertIn('[REDACTED]', out)
        self.assertNotIn('a' * 40, out)
        self.assertLessEqual(len(out), TASK.MAX_CHARS + 200)

    def test_cli_is_shell_safe(self):
        payload = json.dumps(threads([thread('$(exit 9)')]))
        result = subprocess.run([sys.executable, str(ROOT / '.github/scripts/autofix_task.py')],
                                input=payload, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('$(exit 9)', result.stdout)

    def test_workflow_is_disabled_and_isolated(self):
        workflow = (ROOT / '.github/workflows/auto-fix.yml').read_text()
        self.assertIn("vars.AUTOFIX_ENABLED == 'true'", workflow)
        self.assertNotIn('pull_request_target:', workflow)
        self.assertIn('autofix_eligibility.py', workflow)
        self.assertIn('env -u GH_TOKEN', workflow)
        self.assertIn('core.hooksPath=/dev/null', workflow)
        self.assertIn('pull-requests: read', workflow)


if __name__ == '__main__':
    unittest.main()
