# Versioning and releases

Version numbers have two scopes:

| Scope | Source of truth | Example |
|---|---|---|
| Repository release | `hermes.json` → `version` | `1.0.0` |
| Individual plugin | `plugins/<id>/plugin.yaml` → `version` | `1.2.0-test` |

A merge is not a release. Nothing is published or installed by merging a PR.

When workflows are added in separate PRs, land each workflow PR before any PR
whose README badges or `docs/CI.md` entry reference it. A badge or gate table
that points at a workflow not yet on `main` reads as broken until that PR merges.

## Release process

1. Bump `hermes.json` `version` in a normal PR and merge it.
2. Create an annotated tag from the merged `main` commit:
   `git tag -a v1.0.1 -m "AHP v1.0.1" && git push origin v1.0.1`.
3. `.github/workflows/release.yml` runs on the tag, rejects a tag that does not
   match `hermes.json`, and then creates a GitHub Release with generated notes.

Tags are immutable. Do not move or delete a published tag; publish a new patch
version instead. The workflow uses only the repository token, pinned
`actions/checkout`, and the preinstalled `gh` CLI — no third-party release
action.

## Plugin versions

Plugin versions move independently from the repository tag. Update the plugin
manifest when that plugin's behavior changes, and describe the change in its
`docs/USAGE.md` status table. A plugin version alone does not prove compatibility
with a Hermes host; the pinned host commit in `AGENTS.md` is the compatibility
evidence used by CI.

## Documentation site

`site/` is deployed by `.github/workflows/pages.yml` on every `main` push that
changes the site or this documentation. The site is static HTML and makes no
runtime or security claims beyond what the repository documents.
