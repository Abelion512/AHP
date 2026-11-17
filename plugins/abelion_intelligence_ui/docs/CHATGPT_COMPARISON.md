# Comparison — ChatGPT Intelligent UI vs `::ui{...}`

**Source:** conversation with ChatGPT over the user's logged-in browser,
`https://chatgpt.com/c/6afc11cf-db3c-83ec-9d93-d7acbac8e2e5` (2026-11-17).
That answer is an external AI opinion, not an OpenAI specification. ChatGPT
itself said OpenAI does not publish the full internal pipeline; its "DIL"
description comes from third-party reverse engineering. Label: `PERKIRAAN`.

Our side is `TERVERIFIKASI` from local source and the live WebApp e2e recorded
in `CORE_COMPARISON.md`.

| Aspect | ChatGPT answer | Our implementation | Decision |
|---|---|---|---|
| Trigger | Model emits a UI representation (claimed: DIL) | Model emits one-line `::ui{...}` | Keep our syntax; it is the model-facing interface |
| Format | Markup + JS + Markdown | Attr string, `key="value"`, one line | Keep; no JS/HTML from model |
| Compiler | Server-side compiler | Plugin parser in renderer | Not adopted; would be a core change |
| Validation | Component schema + props | `docs/directive-contract.json` + runtime allowlist/caps | Partly adopted; still not a typed AST |
| Runtime | Sandboxed runtime | Native React component | Keep native; sandbox not needed for allowlisted components |
| State | Callback + local state | `ctx.storage` keyed `abelion-intelligence-ui:<version>:<id>` for wizard done | Adopted stable id/key this round |
| Streaming | Incremental compilation | Placeholder while `streaming`, full card after settle | Adopted minimal version |
| Fallback | Partial recovery + text | Unsupported line + core's plain-text fallback | Adopted |
| Security | Never execute model JS | Same: no `eval`, no `fetch`, no HTML from attrs | Already satisfied |

## Gaps ChatGPT named that are still open

1. **Typed UI AST.** We have a versioned JSON contract, but the runtime parser
   does not build a typed AST nor validate a full schema. Attrs are capped and
   the kind is allowlisted; that is weaker than schema validation.
2. **Interaction event types.** `host.composer.submit` is a plain string
   bridge, not a typed event with payload schema.
3. **Form values persistence.** Wizard `done` state is persisted; form inputs
   are intentionally not, to avoid storing user text in plugin storage.
4. **Cross-thread state.** The `id` key is stable within the plugin storage
   namespace, but not tied to a conversation/thread id.

## What we did not adopt

- Building a mini-ChatGPT compiler or DIL-like markup: it adds a second
  language the model must learn and a second runtime to secure.
- Executing model-supplied JavaScript: rejected explicitly by both sides.
- Moving the directive into core: not justified; the plugin seam already works
  and is opt-in (see `CORE_COMPARISON.md`).

## Verdict

ChatGPT's useful contribution is the separation of concerns:
**authoring syntax → validation → runtime state → renderer**. Our plugin now
has the first, a lightweight second, a bounded third, and the fourth. The
remaining work is a real validator/AST, not a different syntax.
