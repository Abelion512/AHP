"""Shallow PR rationale validation. Text completeness is not proof of correctness."""
import os
import re

SECTIONS = {
    'What changed': ('what changed', 'fungsi apa yang dibawa pr ini?'),
    'Why merge this now': ('why merge this now', 'kenapa harus saya merge?'),
    'Changes': ('changes', 'perubahan'),
    'Before / after': ('before / after', 'sebelum / sesudah'),
    'How it works': ('how it works', 'cara kerja', 'bagaimana cara kerjanya'),
    'Verification': ('verification', 'bukti verifikasi'),
    'Trade-off': ('trade-off', 'tradeoff', 'kekurangan'),
    'Checklist': ('checklist', 'daftar periksa'),
}
PLACEHOLDERS = {'todo', 'tbd', 'tba', 'n/a', 'na', 'none', 'placeholder',
                'xxx', 'fixme', 'wip', 'coming soon', 'tbc', 'fixes', 'later', 'null', 'empty'}


def substantive(text):
    # Ignore markup and empty template scaffolding, including unchecked items.
    plain = text.strip().lstrip('-*| ').casefold()
    annotated = any(plain.startswith(word + separator)
                    for word in PLACEHOLDERS for separator in (':', ' -', '.', ';'))
    if annotated or re.match(r'(?:todo|tbd|tba|wip|fixme|placeholder|coming soon|later|null|empty)\b', plain):
        return False
    lines = []
    for line in text.splitlines():
        if re.match(r'^\s*\|?(?:\s*:?-+:?\s*\|)+\s*$', line):
            continue
        if re.match(r'^\s*[-*]\s+\[\s*\]\s*', line):
            continue
        line = re.sub(r'^\s*[-*]\s+\[[xX]\]\s*', '', line)
        words = re.findall(r'[^\W_]+', line.casefold(), re.UNICODE)
        words = [w for w in words if w not in PLACEHOLDERS]
        if words not in (['check', 'result', 'label'], ['before', 'this', 'pr']):
            lines.extend(words)
    return len(lines) >= 3 and len(set(lines)) >= 3 and len(' '.join(lines)) >= 15


def visible_lines(body):
    # Linear scans avoid regex backtracking on an unclosed comment/fence.
    pieces = []
    offset = 0
    while True:
        start = body.find('<!--', offset)
        if start < 0:
            pieces.append(body[offset:])
            break
        pieces.append(body[offset:start])
        end = body.find('-->', start + 4)
        if end < 0:
            break
        offset = end + 3
    fence = None
    for line in ''.join(pieces).splitlines():
        stripped = line.lstrip()
        marker = stripped[:1]
        count = len(stripped) - len(stripped.lstrip(marker)) if marker in ('`', '~') else 0
        if fence:
            char, length = fence
            if marker == char and count >= length and not stripped[count:].strip():
                fence = None
        elif count >= 3:
            fence = (marker, count)
        else:
            yield line


def missing_sections(body):
    sections = {}
    current = None
    for line in visible_lines(body):
        if line.startswith('## ') or line.startswith('##\t'):
            current = line[3:].strip().casefold()
            sections.setdefault(current, []).append([])
        elif current is not None:
            sections[current][-1].append(line)
    return [name for name, aliases in SECTIONS.items()
            if not any(substantive('\n'.join(part)) for alias in aliases
                       for part in sections.get(alias, []))]


def main():
    missing = missing_sections(os.environ.get('PR_BODY', ''))
    if missing:
        print('PR body is incomplete. Fill: ' + ', '.join(missing))
        return 1
    print('Required PR rationale sections contain substantive text. Evidence still needs review.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
