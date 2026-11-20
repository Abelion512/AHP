# Why a plugin

The supported core pin already exports `TRANSCRIPT_DIRECTIVE_AREA`, renderer
props including `sessionId`, and the owner-addressed composer. Aero registers the
unclaimed `ui` name and uses those seams, so no core patch is necessary.

The pinned parser source is copied unchanged in `e2e/fixtures/`, with provenance.
It recognizes inline and stacked directives. Older notes about a one-card parser
limit were stale and have been removed. A single card remains the default
composition guideline, not a host limitation.

The component sketch in `core-ui-reference.tsx` is not imported or compiled.
It is reference material only, not a second supported implementation.

## Scope boundary

The CI/local seam test runs actual pinned parsing plus actual plugin rendering
and actual browser interaction. It substitutes the SDK bridge, so it proves
which owner and payload Aero submits, not live delivery through every host.
Missing owning session ids deliberately refuse actions. A live model may still
fail to discover or follow a bundled skill; no deterministic fixture establishes
its behavior. No active profile, installed plugin or live model was changed by
this PR repair.
