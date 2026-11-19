"""Build a bounded, sanitized task file from review comments.

The output is data for the agent, never shell. HTML comments are stripped and
each body is capped so a single comment cannot dominate the context.
"""
import json
import re
import sys


def build(comments, limit=2000):
    lines = [
        '# Auto-fix task',
        '',
        'Fix only the findings listed below. Keep changes inside the repo and',
        'answer each finding in its own commit. Do not merge.',
        '',
    ]
    for item in comments:
        if not isinstance(item, dict):
            continue
        body = re.sub(r'<!--.*?-->', '', item.get('body') or '', flags=re.DOTALL)
        body = ' '.join(body.split())[:limit]
        where = '%s:%s' % (item.get('path') or '?', item.get('line') or item.get('original_line') or '?')
        lines.append('- %s - %s' % (where, body))
    return '\n'.join(lines) + '\n'


def main(argv):
    if len(argv) != 1:
        print('usage: autofix_task.py < comments.json')
        return 2
    # Read from stdin: a file path would be an untrusted command-line input.
    comments = json.load(sys.stdin)
    sys.stdout.write(build(comments))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
