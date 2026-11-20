"""Fail-closed eligibility for the opt-in auto-fix lane.

Reads a PR JSON object from disk and a trusted repository id. Never reads PR
text as code. Returns a fixed reason constant, never model or PR prose.
"""
import json
import re
import sys


def eligible(pr, repo_id):
    if not isinstance(pr, dict):
        return 'malformed_pr'
    if pr.get('state') != 'open':
        return 'pr_not_open'
    draft = pr.get('draft')
    if type(draft) is not bool:
        return 'malformed_draft'
    if draft:
        return 'draft_pr'
    head = pr.get('head')
    base = pr.get('base')
    if not isinstance(head, dict) or not isinstance(base, dict):
        return 'malformed_ref'
    head_repo = head.get('repo')
    if not isinstance(head_repo, dict) or type(head_repo.get('id')) is not int:
        return 'malformed_head'
    if head_repo['id'] != repo_id:
        return 'fork_head_outside_scope'
    if base.get('ref') != 'main':
        return 'wrong_base'
    count = pr.get('changed_files')
    if type(count) is not int or count <= 0:
        return 'empty_pr'
    return None


def main(argv):
    if len(argv) != 2 or not re.fullmatch(r'[0-9]{1,9}', argv[1]):
        print('usage: autofix_eligibility.py REPO_ID < pr.json')
        return 2
    # Read from stdin: a file path would be an untrusted command-line input.
    pr = json.load(sys.stdin)
    reason = eligible(pr, int(argv[1]))
    if reason:
        print('autofix_not_eligible: ' + reason)
        return 1
    print('autofix_eligible')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
