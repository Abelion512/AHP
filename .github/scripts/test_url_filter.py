"""Regression tests for the credential-guard URL exemption."""
import unittest

from url_filter import strip_url_structure


class UrlFilterTest(unittest.TestCase):
    def test_benign_repo_url_noise_is_removed(self):
        line = '+ <a href="https://github.com/example-org/AHP/blob/main/docs/VERSIONING.md">docs</a>'
        self.assertNotIn("example-org/AHP", strip_url_structure(line))

    def test_url_host_is_removed(self):
        line = "+ see https://docs.github.com/en/actions/reference for details"
        self.assertNotIn("docs.github.com", strip_url_structure(line))

    def test_secret_in_path_is_kept(self):
        secret = "a" * 40
        line = f"+ https://example.com/{secret}/docs"
        self.assertIn(secret, strip_url_structure(line))

    def test_secret_in_query_is_kept(self):
        secret = "b" * 40
        line = f"+ https://example.com/cb?sig={secret}"
        self.assertIn(secret, strip_url_structure(line))

    def test_secret_in_slashless_query_is_kept(self):
        secret = "b" * 40
        line = f"+ https://example.com?sig={secret}"
        self.assertIn(secret, strip_url_structure(line))
        self.assertNotIn("example.com", strip_url_structure(line))

    def test_secret_in_slashless_fragment_is_kept(self):
        secret = "b" * 40
        line = f"+ https://example.com#{secret}"
        self.assertIn(secret, strip_url_structure(line))

    def test_secret_before_benign_marker_is_kept(self):
        secret = "b" * 40
        line = f"+ https://github.com/example-org/{secret}-AHP/blob/main/docs/CI.md"
        self.assertIn(secret, strip_url_structure(line))

    def test_secret_in_userinfo_is_kept(self):
        secret = "c" * 40
        line = f"+ https://user@user:{secret}@example.com/x"
        self.assertIn(secret, strip_url_structure(line))

    def test_secret_in_fragment_before_question_mark_is_kept(self):
        secret = "d" * 40
        line = f"+ https://example.com/x#{secret}?next=1"
        self.assertIn(secret, strip_url_structure(line))

    def test_uppercase_scheme_is_handled(self):
        secret = "e" * 40
        line = f"+ HTTPS://example.com/{secret}"
        self.assertIn(secret, strip_url_structure(line))
        self.assertNotIn("example.com", strip_url_structure(line))

    def test_adjacent_urls_are_separate(self):
        line = "[![ci](https://github.com/o/r/badge.svg?branch=main)](https://github.com/o/r)"
        stripped = strip_url_structure(line)
        self.assertEqual(stripped.count("/o/r"), 2)
        self.assertNotIn("](https", stripped)

    def test_secret_outside_url_is_kept(self):
        secret = "f" * 40
        line = f"+ TOKEN = {secret}"
        self.assertIn(secret, strip_url_structure(line))


if __name__ == "__main__":
    unittest.main()
