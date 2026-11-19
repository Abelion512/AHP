# Visual-learning design

This document records the original eight `ui` kinds. The added media directives, external image loading and their separate acceptance gaps are scoped in [PHOTO-VERIFICATION.md](PHOTO-VERIFICATION.md).

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

## Interaction contract (current build)

This section records how each visible element behaves today, which behaviors
come from the ChatGPT/Gemini references, and which are deliberate extensions
requested for this plugin. References were re-checked against live sessions on
2026-11-18/19.

### Reference patterns

- ChatGPT product cards: only the product image is clickable; it opens a full
  image viewer whose footer carries a small domain + listing source link.
  Title, price and specs are plain text. There is no product-detail popup and
  no source button on the card itself.
- ChatGPT quiz/interview: lettered options, a next control anchored
  bottom-right, selections stay local until submit.
- Gemini quiz: live score in the header with a thin progress bar under it.
- Gemini place cards: tapping a place opens a rich side panel with labeled
  pill actions (Directions, Website, Open in Google Maps). Detail lives in the
  panel, not on the card.

### Shipped extensions (requested, beyond both references)

| Element | Click behavior | Status |
|---|---|---|
| Product card body (title/specs area) | Opens a detail dialog with the full description and the source link | Shipped, host-verified |
| Product image | Opens the image viewer ONLY (detail dialog does not open) | Shipped, host-verified |
| Source link | Rendered as a labeled button carrying the real URL; raw URLs are never shown | Shipped; final label wording pending user decision |
| Interview options | Lettered (A., B., ...) unless the title already starts with a letter marker; native radios, no custom focus decoration | Shipped, host-verified |
| Interview submit | Disabled until every group has a pick; enabled state is solid black; submit posts the answer as a chat message ("Jawaban: ...") | Shipped, host-verified |
| Quiz | Header shows "Soal X dari Y · Skor: N" with a thin progress bar; correct answer turns green, wrong answer red; "Berikutnya" bottom-right; completion screen shows "Skor N dari N" with "Ulangi" | Shipped, host-verified |

### Layout rules

- Black only for emphasis (enabled submit, primary actions). No Apple-blue.
- Simplest possible rendering: native inputs, no extra focus frames when a
  label and description sit adjacent.
- Plugin roots keep right clearance from the host conversation-timeline rail:
  measured 42-44px at 390px width, 42px (grid) / 244px (cards) at 1280px.
- Two-column title/description layouts apply only on wide viewports; 390px
  stacks vertically with no horizontal overflow (document width stays 390).

### Support status per kind

Supported `ui` kinds: wizard, status, compare, form, trace, choice, flow,
chart, interview, quiz, table, map, plus the `visualcards` media directive.
`table` renders a bounded headered data table (max 5 columns x 8 rows);
`chart` still offers its own table alternative. Table cells never wrap
(bounded by the 60-character cell contract): a table that fits the pane
renders full-width with no scrolling, and a table wider than the pane
scrolls horizontally inside the card instead of compressing. `map` takes 1-5 places as
name;latitude;longitude with an optional note and renders a STATIC 3x3
OpenStreetMap tile grid with labeled pins - the renderer builds the tile URLs
itself (the model never supplies URLs), shows a visible
"© OpenStreetMap contributors" attribution, and is labeled "Peta statis". It
is not interactive-map parity with the GPT/Gemini references (no pan/zoom,
no place side panel with photos, hours or Directions/Website/Call actions).
Checked against the live OSM Tile Usage Policy
(operations.osmfoundation.org/policies/tiles/): within this bounded
demonstration (9 tiles per map, no bulk download or prefetch) the static
map follows every MUST - correct HTTPS tile URL template, visible
attribution with the copyright link, browser-default User-Agent and
Referer (tile images carry no referrerPolicy, unlike card images), and
browser-default caching. Two should-level gaps remain: the tile URL is
hardcoded rather than configurable, and there is no fixthemap link. The
OSM tile service is volunteer-run and best-effort with no SLA and its own
usage limits, so this is a scoped compliance note for the plugin's bounded
use, not a production-scale availability guarantee. There is no video-embed kind either: the GPT reference embeds a playable
YouTube iframe, and this plugin does not embed third-party players. There is
no calendar or generic-widget kind. Unsupported or malformed directives fall
back to visible text, never to a broken frame.

Fixture-rendered kinds are verified with the deterministic harness and host
screenshots. Live-model generation of directives is tracked separately; the
desktop renderer does not depend on which model produced the directive.

Host rendering constraints (v0.23.2, demonstrated in the harness, not
plugin-fixable): the host only segments a paragraph into directives when the
paragraph is text-only, and its soft-break preprocessing turns a single
newline into a break node. Two directives one newline apart - or a directive
with prose on the next line - therefore share a paragraph and none of them
render; they remain raw text. Directives must be blank-line separated (the
SKILL.md authoring rule). A directive missing its closing brace is never
claimed: it stays raw text by design, and it does not stop other directives
in the same message from rendering (harness-verified). A paragraph over
4800 characters is not segmented
at all, one brace body is capped at 2048 characters, and attribute values
cannot contain braces. Unsupported or unregistered directive names stay
visible raw text by host design.

### Skill discovery contract (model-facing)

Hermes clips every skill description to 60 characters
(`SKILL_PROMPT_DESC_LIMIT`) in the system prompt's `<available_skills>` index,
so `_SKILL_DESCRIPTION` in `__init__.py` leads with the exact qualified load
string `skill_view('aero:aero')` followed by trigger words (kartu, kuis,
tabel, peta, form). Plugin skills resolve in `skill_view` only under the
qualified `plugin:skill` name; a bare `skill_view('aero')` misses the plugin
registry and fails with "not found", after which models fall back to building
HTML file artifacts. When the task matches, the model must emit `::ui`
directives inline in the chat answer, never a separate HTML file.
