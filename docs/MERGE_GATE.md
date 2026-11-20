# Merge gate

A single check named `merge-gate` is published on every open PR. It is green only when:

- all expected check runs are completed and successful (`success`, `skipped` or `neutral`);
- no review thread is unresolved;
- no reviewer has outstanding `CHANGES_REQUESTED`;
- at least one human approval exists, excluding the PR author and bots;
- the PR is not a draft and has no merge conflict.

The workflow `.github/workflows/merge-gate.yml` runs on PR changes, review events, check completions, related workflow completions and a 15-minute timer. It evaluates the PR head SHA and publishes the result with the Checks API.

## Required repository configuration

The check only blocks merge if the branch ruleset requires it. In the `main-owner-only` ruleset:

- add `merge-gate` to **Require status checks to pass**;
- set **Required approving reviews** to 1;
- enable **Resolve conversations before merge**.

Until that configuration is applied, the check is advisory. The repository ruleset cannot be edited through the current automation token, so an owner must apply it in Settings → Rules → Rulesets.

## Troubleshooting

- **missing check** — a required workflow did not run; check the workflow's path filters and re-run it.
- **status=in_progress** — wait for the check to finish.
- **unresolved review thread** — reply and resolve the thread in GitHub.
- **changes requested** — the reviewer must approve or dismiss the review.
- **no human approval** — a bot approval does not count; a human with write access must approve.
