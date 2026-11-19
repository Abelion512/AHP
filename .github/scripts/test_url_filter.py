"""Regression tests for the credential-guard URL exemption."""
import unittest

from url_filter import strip_url_structure


class UrlFilterTest(unittest.TestCase):
    def test_benign_url_path_is_removed(self):
        line = "+ see https://github.com/Abelion512/AHP/blob/main/docs/CI.md for details"
        self.assertNotIn("Abelion512", strip_url_structure(line))

    def test_secret_in_query_is_kept(self):
        secret = "a" * 40
        line = f"+ https://example.com/cb?sig={secret}"
        self.assertIn(secret, strip_url_structure(line))

    def test_secret_in_userinfo_is_kept(self):
        secret = "b" * 40
        line = f"+ https://user:{secret}@example.com/x"
        self.assertIn(secret, strip_url_structure(line))

    def test_secret_in_fragment_is_kept(self):
        secret = "c" * 40
        line = f"+ https://example.com/x#{secret}"
        self.assertIn(secret, strip_url_structure(line))

    def test_secret_outside_url_is_kept(self):
        secret = "d" * 40
        line = f"+ TOKEN = {secret}"
        self.assertIn(secret, strip_url_structure(line))


if __name__ == "__main__":
    unittest.main()
