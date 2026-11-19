"""Build a bounded, sanitized task file from unresolved review threads.

Input is GraphQL review-thread JSON on stdin. Resolved and outdated threads are
dropped, secret-shaped text is redacted, and both comment count and total size
are capped. Output is data for the agent, never shell.
"""
import json
import re
import sys

MAX_COMMENTS = 20
MAX_CHARS = 12000
MAX_BODY = 1500
SECRET = re.compile(
    r'-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----'
    r'|(?:gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{10,})'
    r'|\b[0-9a-fA-F]{40,}\b',
)


def redact(text):
    return SECRET.sub('[REDACTED]', text)


def build(threads, limit=MAX_BODY):
    data = (threads.get('data') or {}).get('repository') or {}
    pull = data.get('pullRequest') or {}
    nodes = ((pull.get('reviewThreads') or {}).get('nodes') or [])
    lines = [
        '# Auto-fix task',
        '',
        'Fix only the findings listed below. Keep changes inside the repo and',
        'answer each finding in its own commit. Do not merge.',
        '',
    ]
    used = 0
    count = 0
    for thread in nodes:
        if not isinstance(thread, dict) or thread.get('isResolved') or thread.get('isOutdated'):
            continue
        for comment in ((thread.get('comments') or {}).get('nodes') or []):
            if not isinstance(comment, dict) or count >= MAX_COMMENTS:
                break
            body = re.sub(r'<!--.*?-->', '', comment.get('body') or '', flags=re.DOTALL)
            body = ' '.join(redact(body).split())[:limit]
            where = '%s:%s' % (comment.get('path') or '?', comment.get('line') or comment.get('originalLine') or '?')
            entry = '- %s - %s\n' % (where, body)
            if used + len(entry) > MAX_CHARS:
                lines.append('- Task budget reached; remaining findings omitted.')
                return '\n'.join(lines) + '\n'
            lines.append(entry.rstrip('\n'))
            used += len(entry)
            count += 1
    return '\n'.join(lines) + '\n'


def main(argv):
    if len(argv) != 1:
        print('usage: autofix_task.py < threads.json')
        return 2
    threads = json.load(sys.stdin)
    sys.stdout.write(build(threads))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
