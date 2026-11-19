import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ProofRetryTest(unittest.TestCase):
    def test_retries_only_the_comment_race(self):
        workflow = (ROOT / '.github/workflows/stronsium-proof.yml').read_text()
        self.assertIn('producer_comments_changed', workflow)
        self.assertIn('for attempt in 1 2 3 4', workflow)
        self.assertIn('grep -q', workflow)
        self.assertIn('every other failure stays fatal', workflow)


if __name__ == '__main__':
    unittest.main()
