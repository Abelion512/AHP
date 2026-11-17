import importlib.util
from pathlib import Path
import os
import subprocess
import sys
import unittest
import time

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / '.github/scripts/check_pr_body.py'
spec = importlib.util.spec_from_file_location('pr_body', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def body(answer='Meaningful implementation evidence from actual tests.', legacy=False):
    headings = ['Fungsi apa yang dibawa PR ini?', 'Kenapa harus saya merge?', 'Bukti verifikasi'] if legacy else list(module.SECTIONS)
    return '\n'.join('## ' + heading + '\n' + answer for heading in headings)


class BodyCheckTest(unittest.TestCase):
    def test_canonical(self):
        self.assertEqual(module.missing_sections(body()), [])

    def test_legacy(self):
        self.assertEqual(module.missing_sections(body(legacy=True)), [])

    def test_missing(self):
        self.assertEqual(len(module.missing_sections('')), 3)

    def test_all_scaffolds(self):
        for answer in ['', 'TODO', 'TODO: implementation will be added', 'WIP - details will follow', 'later with more information', 'coming soon', 'abcdefghijklmnopqrst', 'wip wip wip', '- [ ]', '| check | result | label |\n|---|---|---|\n| | | |', '<!-- Actual meaningful evidence but commented -->']:
            with self.subTest(answer=answer):
                self.assertEqual(len(module.missing_sections(body(answer))), 3)

    def test_blank_canonical_template(self):
        self.assertEqual(len(module.missing_sections((ROOT / '.github/PULL_REQUEST_TEMPLATE.md').read_text())), 3)

    def test_new_section_does_not_fill_previous(self):
        value = body().replace('## What changed\nMeaningful implementation evidence from actual tests.', '## What changed\n## Unrelated\nMeaningful implementation evidence from actual tests.')
        self.assertEqual(module.missing_sections(value), ['What changed'])

    def test_fake_commented_headings(self):
        self.assertEqual(len(module.missing_sections('<!--' + body() + '-->')), 3)

    def test_code_block_headings(self):
        self.assertEqual(len(module.missing_sections('```markdown\n' + body() + '\n```')), 3)

    def test_long_unclosed_fence_and_comment_are_bounded(self):
        for value in ['<!--' + 'x' * 250000, '```markdown\n' + body() + '\n' + ' ' * 250000]:
            start = time.monotonic()
            self.assertEqual(len(module.missing_sections(value)), 3)
            self.assertLess(time.monotonic() - start, 3)

    def test_tilde_fences_and_unclosed_fences(self):
        for value in ['~~~markdown\n' + body() + '\n~~~', '```markdown\n' + body()]:
            self.assertEqual(len(module.missing_sections(value)), 3)

    def test_crlf_case(self):
        self.assertEqual(module.missing_sections(body().upper().replace('\n', '\r\n')), [])

    def test_cli_and_literal_untrusted_body(self):
        for value, expected in [(body() + '\n$(exit 99); `exit 88`', 0), ('', 1)]:
            result = subprocess.run([sys.executable, str(SCRIPT)], env={**os.environ, 'PR_BODY': value}, capture_output=True, text=True)
            self.assertEqual(result.returncode, expected, result.stdout + result.stderr)

    def test_workflow_uses_literal_env_and_readonly_pr_event(self):
        workflow = (ROOT / '.github/workflows/pr-body-check.yml').read_text()
        self.assertIn('  pull_request:', workflow)
        self.assertNotIn('pull_request_target:', workflow)
        self.assertIn('  contents: read', workflow)
        self.assertIn('persist-credentials: false', workflow)
        self.assertIn('run: python .github/scripts/check_pr_body.py', workflow)
        self.assertIn('PR_BODY: ${{ github.event.pull_request.body', workflow)
        self.assertNotIn('run: ${{', workflow)

    def test_single_template(self):
        templates = [p.name for p in (ROOT / '.github').iterdir() if p.name.casefold() == 'pull_request_template.md']
        self.assertEqual(templates, ['PULL_REQUEST_TEMPLATE.md'])


if __name__ == '__main__':
    unittest.main()
