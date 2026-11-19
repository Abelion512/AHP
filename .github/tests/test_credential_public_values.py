"""Exercise the actual inline credential scanner with public-value and secret controls."""
import ast
import contextlib
import io
import os
from pathlib import Path
import textwrap
import unittest
from unittest.mock import patch

WORKFLOW = Path(__file__).resolve().parents[1] / 'workflows' / 'ci.yml'


def scanner():
    source = WORKFLOW.read_text()
    start = source.index("          python - <<'PY' || exit 7")
    block = source[start:].split('\n', 1)[1].split('\n      - name:', 1)[0]
    return textwrap.dedent(block)


def public_values():
    tree = ast.parse(scanner())
    node = next(node for node in tree.body if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == 'public_values' for target in node.targets))
    return ast.literal_eval(node.value)


class CredentialPublicValues(unittest.TestCase):
    def scan(self, path, line):
        diff = 'diff --git a/' + path + ' b/' + path + '\n--- a/' + path + '\n+++ b/' + path + '\n+' + line + '\n'
        return self.scan_diff(diff)

    def scan_diff(self, diff):
        with patch.dict(os.environ, {'PR_BASE': 'base'}), patch('subprocess.check_output', return_value=diff), contextlib.redirect_stdout(io.StringIO()):
            try:
                exec(compile(scanner(), str(WORKFLOW), 'exec'), {})
                return 0
            except SystemExit as result:
                return result.code

    def test_exact_public_values_only_on_owned_paths(self):
        for path, values in public_values().items():
            for value in values:
                with self.subTest(path=path, value=value[:15]):
                    self.assertEqual(self.scan(path, 'value="' + value + '"'), 0)
                    self.assertEqual(self.scan('unrelated.py', 'value="' + value + '"'), 7)

    def test_appended_or_prepended_secrets_still_rejected(self):
        secrets = ['ghp_' + 'Q' * 30, 'sk-proj-' + 'R' * 30, 'hf_' + 'S' * 25,
                   'xoxb-' + 'T' * 20, 'AIza' + 'U' * 32, 'AKIA' + 'V' * 16,
                   'e' * 64, 'Z' * 40]
        for path, values in public_values().items():
            for value in values:
                for secret in secrets:
                    with self.subTest(path=path, secret=secret[:8]):
                        self.assertEqual(self.scan(path, 'value="' + value + '" token="' + secret + '"'), 7)
                        self.assertEqual(self.scan(path, 'token="' + secret + '" value="' + value + '"'), 7)

    def test_changed_or_extended_public_value_is_not_exempt(self):
        for path, values in public_values().items():
            for value in values:
                changed = value.replace('https://assets.', 'https://other.') if value.startswith('https:') else 'a' + value[1:]
                self.assertEqual(self.scan(path, 'value="' + changed + '"'), 7)
                self.assertEqual(self.scan(path, 'value="' + value + '?token=extra"'), 7)

    def test_scanner_declarations_are_checked_except_exact_public_tokens(self):
        for values in public_values().values():
            for value in values:
                self.assertEqual(self.scan('.github/workflows/ci.yml', '    "' + value + '",'), 0)
                self.assertEqual(self.scan('.github/workflows/ci.yml', '    "' + value + '", token="' + 'ghp_' + 'W' * 30 + '"'), 7)

    def test_new_file_header_cannot_reuse_previous_path_exemption(self):
        path, values = next(iter(public_values().items()))
        value = values[0]
        diff = 'diff --git a/' + path + ' b/' + path + '\n+++ b/' + path + '\n+value="' + value + '"\ndiff --git a/not-allowed.py b/not-allowed.py\n+++ b/not-allowed.py\n+value="' + value + '"\n'
        self.assertEqual(self.scan_diff(diff), 7)

    def test_conservative_token_boundaries(self):
        for path, values in public_values().items():
            for value in values:
                for glue in ['+', '=', '.', '%', '/', '-', '_', '?', '#', '&']:
                    with self.subTest(path=path, glue=glue):
                        self.assertEqual(self.scan(path, 'AB' + glue + value + glue + 'CD'), 7)

    def test_diff_headers_cannot_carry_or_forge_path_scope(self):
        path, values = next(iter(public_values().items()))
        value = values[0]
        allowed = 'diff --git a/' + path + ' b/' + path + '\n+++ b/' + path + '\n'
        for header in ['diff --git a/other b/other', 'diff --git "a/space path" "b/space path"']:
            self.assertEqual(self.scan_diff(allowed + header + '\n+++ "b/space path"\n+value="' + value + '"\n'), 7)
        forged = 'diff --git a/other b/other\n+++ b/other\n@@ -0,0 +1,2 @@\n+++ b/' + path + '\n+value="' + value + '"\n'
        self.assertEqual(self.scan_diff(forged), 7)
        self.assertEqual(self.scan_diff(allowed + '@@ -0,0 +1 @@\n+++ token="' + 'ghp_' + 'Q' * 30 + '"\n'), 7)

    def test_actual_current_diff_passes_reviewed_public_exceptions(self):
        import subprocess
        root = WORKFLOW.parents[2]
        base = os.environ.get('PR_BASE') or subprocess.check_output(['git', 'merge-base', 'HEAD', 'origin/main'], cwd=root, text=True).strip()
        actual = subprocess.check_output(['git', 'diff', '--unified=0', base, '--', '.', ':!plugins/aero/tests/runtime/node_modules'], cwd=root, text=True)
        self.assertEqual(self.scan_diff(actual), 0)


if __name__ == '__main__':
    unittest.main()
