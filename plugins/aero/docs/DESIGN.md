# Visual-learning design

## What changed

A card must make a relationship or choice easier to explore, not merely put a
paragraph inside a border. The new primitives add three distinct interactions:

| Question | Representation | User action | Model call |
|---|---|---|---|
| Which direction fits? | Single/multi-choice interview | Select, optionally annotate, explicitly submit | Only on submit |
| How does this process connect? | Ordered stages with arrows | Reveal one stage's explanation | None |
| How do these quantities compare? | Zero-based bars with exact values and source | Focus one value or open equivalent table | None |

Each card has one job. The model chooses the kind from the question and supplies
bounded data; it never supplies JavaScript, HTML, CSS, component imports, network
addresses or formulas. Unknown/malformed data produces a visible fallback.

## Source-informed decisions

- [OpenUI introduction](https://www.openui.com/docs) describes a component library,
  model generation, validation and progressive rendering. Aero adopts the allowed
  component boundary and local exploration, not the entire runtime.
- [OpenUI agent setup](https://www.openui.com/docs/build-agents/ui-generation)
  describes sharing the same component library between model guidance and
  renderer. Aero exports a frozen catalog; its skill and JSON contract have
  consistency tests. Prompt generation is still authored guidance, not a
  schema-derived backend or a claim of complete OpenUI interoperability.
- [OpenUI getting started](https://www.openui.com/docs/getting-started) separates
  library, backend generation and renderer. Aero retains Hermes' existing
  transcript parser, model provider and chat shell. No extra gateway or paid
  service is introduced.
- [OpenUI's Intelligent UI analysis](https://www.openui.com/blog/how-chatgpt-intelligent-ui-works)
  distinguishes local state changes from an explicit new conversation turn.
  Aero uses that distinction: choice selection stays local until submit;
  process/chart exploration never invokes the composer. The analysis is a
  third-party reverse-engineering account, not official confirmation of
  ChatGPT's internal implementation or a compatibility contract.
- [OpenUI source](https://github.com/thesysdev/openui/) is the framework reference,
  not an additional dependency in this plugin.

The source references were read on 2026-11-18. Vendor claims about performance,
production reliability or model accuracy are not adopted as measured results.

## Data and event boundaries

The three new kinds normalize into explicit typed records before rendering.
Choice options must be distinct. Flow nodes/details and chart labels/values
must pair exactly, with no silently dropped rows or synthesized values. Numeric
input permits bounded nonnegative decimals only. Bars share one maximum and a
zero baseline, including sub-unit quantities; an all-zero set stays zero.
Exact values remain visible, with a data-table alternative. Source labels are
untrusted display text, not source verification. The assistant must still ground
the underlying numbers, or label fictional teaching data as illustrative.

Selection, notes, focused stage/bar and table state are ephemeral and reset when
card/owner inputs change. Only the established wizard completion state persists.
Native inputs and buttons support keyboard operation; chart values are readable
without color. Mobile sequences stack vertically and rotate arrows so the order
is not implied incorrectly by a wrapped row. Comprehensive assistive-technology
coverage is still unverified.

Choice submit sends a bounded plain-text answer to the owning session only.
Missing owner, composer refusal, exceptions and oversized payloads fail closed.
The bridge is not a typed action protocol, approval token or permission to
execute external work. Existing host/user approval rules still apply. Duplicate
explicit submit clicks can produce duplicate chat messages, as with existing
forms; no server-side idempotency guarantee is claimed.

## Deliberate limits

This is a bounded first expansion, not full OpenUI parity: no arbitrary UI tree,
branching graph, map, live data binding, slider simulator, image retrieval,
external link execution, shared multi-user state or partial UI patch engine.
Streaming keeps controls unavailable until the complete card is ready. A safe
text fallback is preferable to an unsupported or misleading picture.

The deterministic harness exercises every new primitive, but the new kinds have
not yet been evaluated with a live model/provider. The earlier authorized live
wizard smoke belongs to the recorded five-kind baseline. No claim of improved
learning outcomes is made without user testing or comparative measurements.

Possible later steps: schema-derived prompts, typed host events, more measured
model-selection cases and comprehension/usability checks using real questions.
These should follow evidence, not a growing count of card kinds.
