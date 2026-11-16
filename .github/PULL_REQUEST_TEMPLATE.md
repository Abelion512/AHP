## What changed

<!-- One paragraph a stranger can read in 20 seconds: the problem, why this
     approach, and what to hold in their head while reviewing. Link the issue
     if there is one. -->

Fixes #

## Changes

<!-- Per file or per area, one line each, with the reason - not a diff dump. -->

-

## Before / after

<!-- A two-column table beats prose whenever behaviour changed. Delete the
     section only if nothing observable changed. -->

| | before | this PR |
|---|---|---|
| | | |

## How it works

<!-- Required. Attach a real image of how this change works end to end: a small diagram, or a screenshot of the result. For config or docs changes, a small accurate diagram of what changes is enough. Do not paste a Mermaid block. Keep the editable source in the repo so the next person can regenerate the image. -->

## Infographic

<!-- EVERY PR carries a picture a reviewer can look at without running the code:
     a before/after collage for UI work, the annotated flow for anything that
     moves data or control, a screenshot or graph for an endpoint, a model or a
     fix. Paste the image, never a Mermaid block - GitHub does not render Mermaid
     in comments and only sometimes in a body. Keep the source (mermaid/script)
     in the repo so the next person re-shoots it instead of redrawing it. -->

## Verification

<!-- Facts, not adjectives. Paste the command and its result, and say plainly
     what was NOT covered. A live check that compares old and new behaviour is
     worth more than a green suite. -->

| check | result |
|---|---|
| | |

## Trade-off

<!-- What this gives up, stated plainly. If nothing, say "none" and why. -->

## Checklist

- [ ] Commits follow Conventional Commits (`fix(scope):`, `feat(scope):`)
- [ ] PR title is the same conventional form as the main commit
- [ ] Only changes related to this fix/feature; no drive-by edits
- [ ] Tests added or updated for the changed behaviour
- [ ] CI is green
- [ ] Docs updated where behaviour or setup changed - or N/A
- [ ] Review bot / reviewer findings answered in-thread and fixed in their own commit
