"""Semantic no-behavior lane for P4, trusted application code (runs from the pinned default-branch commit).
It proves ONE narrow thing: every changed file is an existing Python file whose AST is IDENTICAL before and after
(comment, blank-line, whitespace and formatting changes only). Candidate bytes are parsed with ast.parse, never run.
Everything it cannot prove is a refusal, not a pass:
  - non-.py files (docs/.md can be loaded as agent instructions or prompts; no executable-semantics proof exists),
  - added/removed/renamed files, mode/binary changes,
  - docstring or string changes (they are part of the AST), a changed encoding cookie/shebang (first 2 lines),
  - a diff that does not reverse-apply exactly onto the head source (so the base is derived, not trusted).
It is the replacement for the withdrawn path/extension classifier. It does not decide that the change is wanted.

THREAT MODEL / LIMITS (explicit, unresolved for the owner): AST identity is NOT a universal no-behavior proof.
Behavior can depend on text outside the AST: inspect.getsource/linecache/tracebacks/co_firstlineno (line numbers shift when lines
are added/removed), code that reads its own file, and tool-directive comments (type: ignore, noqa, pragma, fmt:, pylint:, mypy:,
nosec, isort:) that change what linters/formatters/coverage do. This lane therefore refuses files that mention source-reading
APIs and any change to a directive comment, but it cannot see runtime reflection built from strings or external readers of the file.
The remaining "observational scope" (line-number and external-tool visibility) is an owner decision, so
OBSERVATIONAL_SCOPE_OWNER_ACCEPTED stays False and the Approve gate keeps denying until a merged PR flips it.
Docs, markdown, YAML and every non-.py file are NOT covered by this lane: legitimate docs-only P4 PRs stay denied (no proof exists)."""

OBSERVATIONAL_SCOPE_OWNER_ACCEPTED = False
import ast
import re

HUNK = re.compile(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?: .*)?')


def _sections(diff):
    out = {}
    for sec in re.split(r'(?m)^(?=diff --git )', diff):
        if not sec.strip():
            continue
        header = sec.partition('\n')[0]
        prefix = 'diff --git a/'
        names = header[len(prefix):].split(' b/') if header.startswith(prefix) else []
        if len(names) != 2 or not names[0] or names[0] != names[1] or names[0] in out:
            raise ValueError('p4_sem_diff_header')
        for bad in ('\nold mode ', '\nnew mode ', '\nnew file mode', '\ndeleted file mode', '\nrename ',
                    '\ncopy ', '\nsimilarity ', '\nBinary files', '\nGIT binary patch'):
            if bad in '\n' + sec:
                raise ValueError('p4_sem_structural_change')
        out[names[0]] = sec
    return out


def reverse_apply(head_text, section):
    """Derive base text only from complete, ordered, internally consistent hunks.

    Missing-newline markers are refused rather than silently normalizing evidence.
    """
    head = head_text.replace('\r\n', '\n').splitlines()
    lines = section.splitlines()
    i = next((n for n, line in enumerate(lines) if HUNK.match(line)), len(lines))
    if i == len(lines):
        raise ValueError('p4_sem_no_hunks')
    hunks = []
    previous_old_end = previous_new_end = delta = 0
    while i < len(lines):
        match = HUNK.fullmatch(lines[i])
        if not match:
            raise ValueError('p4_sem_hunk_syntax')
        oldstart, oldlen, newstart, newlen = (
            int(match.group(1)), int(match.group(2) or 1),
            int(match.group(3)), int(match.group(4) or 1))
        oldpos = oldstart - 1 if oldlen else oldstart
        newpos = newstart - 1 if newlen else newstart
        if (oldpos < previous_old_end or newpos < previous_new_end
                or oldpos < 0 or newpos < 0 or newpos > len(head)
                or newpos != oldpos + delta):
            raise ValueError('p4_sem_hunk_range')
        old, new = [], []
        i += 1
        while i < len(lines) and not lines[i].startswith('@@ '):
            line = lines[i]
            tag, body = line[:1], line[1:]
            if tag == ' ':
                old.append(body)
                new.append(body)
            elif tag == '-':
                old.append(body)
            elif tag == '+':
                new.append(body)
            else:
                raise ValueError('p4_sem_hunk_line')
            i += 1
        if len(old) != oldlen or len(new) != newlen:
            raise ValueError('p4_sem_hunk_length')
        if head[newpos:newpos + newlen] != new:
            raise ValueError('p4_sem_diff_does_not_match_source')
        hunks.append((newpos, old, newlen))
        previous_old_end = oldpos + oldlen
        previous_new_end = newpos + newlen
        delta += newlen - oldlen
    base = list(head)
    for position, old, newlen in reversed(hunks):
        base[position:position + newlen] = old
    return '\n'.join(base) + ('\n' if head_text.endswith('\n') else '')


def _tree(text):
    try:
        return ast.dump(ast.parse(text.replace('\r\n', '\n')), include_attributes=False)
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        raise ValueError('p4_sem_unparseable')


_SOURCE_READING = re.compile(r'\b(inspect|linecache|getsource|getsourcelines|getsourcefile|traceback|co_firstlineno|f_lineno|tb_lineno|'
                             r'__file__|_getframe|currentframe|__doc__|getdoc|pydoc|doctest|exec|eval|compile)\b')
_DIRECTIVE = re.compile(r'#.*\b(type:\s*ignore|noqa|pragma|fmt:|yapf:|isort:|pylint:|mypy:|pyright:|ruff:|flake8|nosec|nosemgrep|'
                        r'cython:|coding[:=]|-\*-)', re.I)


def _directive_lines(text):
    return [(i, l) for i, l in enumerate(text.replace('\r\n', '\n').split('\n')) if _DIRECTIVE.search(l)]


def _header(text):
    """Shebang and PEP 263 encoding-cookie lines among the first two lines (they change decoding/exec, not the AST)."""
    first = text.replace('\r\n', '\n').split('\n')[:2]
    return [(i, l) for i, l in enumerate(first) if l.startswith('#!') or re.search(r'coding[:=]\s*[-\w.]+', l)]


def classify_semantic(context):
    """Return {'scope','findings'} when every file is AST-identical, else raise ValueError(reason)."""
    if context['finding_ids']:
        raise ValueError('open_findings_unverified')
    secs = _sections(context['diff'])
    paths = [f['filename'] for f in context['paths']]
    if sorted(secs) != sorted(paths):
        raise ValueError('p4_sem_diff_path_mismatch')
    for f in context['paths']:
        p = f['filename']
        if f['status'] != 'modified':
            raise ValueError('p4_sem_status_not_modified')
        if not p.endswith('.py'):
            raise ValueError('p4_sem_not_python:' + p)
        head = context['sources'][p]
        base = reverse_apply(head, secs[p])
        if _tree(base) != _tree(head):
            raise ValueError('p4_sem_ast_changed:' + p)
        if _SOURCE_READING.search(base) or _SOURCE_READING.search(head):
            raise ValueError('p4_sem_source_sensitive:' + p)
        if _directive_lines(base) != _directive_lines(head):
            raise ValueError('p4_sem_directive_comment_changed:' + p)
        if _header(base) != _header(head):
            raise ValueError('p4_sem_header_lines_changed:' + p)
    return {'scope': {'classification': 'P4_python_ast_equivalent', 'ast_equivalent_only': True,
                      'coverage_complete': True,
                      'reasons': ['Every changed file is an existing .py file whose AST is identical before and after '
                                  '(derived by reverse-applying the diff); only comments/whitespace/formatting changed. Observational scope '
                                  '(line numbers, external readers) is NOT verified.']},
            'findings': []}
