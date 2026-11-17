"""Shallow PR rationale validation. Text completeness is not proof of correctness."""
import os
import re

SECTIONS = {
    'What changed': ('what changed', 'fungsi apa yang dibawa pr ini?'),
    'Why merge this now': ('why merge this now', 'kenapa harus saya merge?'),
    'Verification': ('verification', 'bukti verifikasi'),
}
PLACEHOLDERS = {'todo', 'tbd', 'tba', 'n/a', 'na', 'none', 'placeholder',
                'xxx', 'fixme', 'wip', 'coming soon', 'tbc', 'fixes', 'later', 'null', 'empty'}


def substantive(text):
    # Ignore markup and empty template scaffolding, including unchecked items.
    plain = text.strip().lstrip('-*| ').casefold()
    if re.match(r'(?:todo|tbd|tba|wip|fixme|placeholder|coming soon|later|null|empty)\b', plain):
        return False
    lines = []
    for line in text.splitlines():
        if re.match(r'^\s*\|?(?:\s*:?-+:?\s*\|)+\s*$', line):
            continue
        line = re.sub(r'^\s*[-*]\s+\[[ xX]\]\s*', '', line)
        words = re.findall(r'[^\W_]+', line.casefold(), re.UNICODE)
        words = [w for w in words if w not in PLACEHOLDERS]
        if words not in (['check', 'result', 'label'], ['before', 'this', 'pr']):
            lines.extend(words)
    return len(lines) >= 3 and len(set(lines)) >= 3 and len(' '.join(lines)) >= 15


def missing_sections(body):
    visible = re.sub(r'<!--.*?(?:-->|\Z)', '', body, flags=re.S)
    # Code examples cannot supply fake headings or rationale.
    visible = re.sub(r'(?ms)^\s*(`{3,}|~{3,}).*?^\s*\1\s*$', '', visible)
    chunks = re.split(r'(?m)^##[ \t]+([^\n]+)\n?', visible)
    sections = {}
    for index in range(1, len(chunks), 2):
        sections.setdefault(chunks[index].strip().casefold(), []).append(chunks[index + 1])
    return [name for name, aliases in SECTIONS.items()
            if not any(substantive(part) for alias in aliases for part in sections.get(alias, []))]


def main():
    missing = missing_sections(os.environ.get('PR_BODY', ''))
    if missing:
        print('PR body is incomplete. Fill: ' + ', '.join(missing))
        return 1
    print('Required PR rationale sections contain substantive text. Evidence still needs review.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
