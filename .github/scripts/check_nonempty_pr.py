"""Fail a PR with no tree diff against its base.

An empty PR cannot produce a stronsium proof: the producer's eligibility check
rejects changed_files == 0 as malformed. Such a PR only creates review noise.
"""
import os
import sys


def main():
    raw = os.environ.get('PR_CHANGED_FILES', '')
    if not raw.isdigit() or int(raw) <= 0:
        print('PR has no changed files against its base. Merge or close it instead.')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
