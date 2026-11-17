# Core comparison — why this is a plugin

The directive is versioned: `::ui{version="1" id="..." kind="..."}`. The full
model-facing contract is `docs/directive-contract.json`.

## Decision: plugin, not core

Data observed on Hermes v0.23.1:

| Question | Evidence | Verdict |
|---|---|---|
| Is there a host seam for native inline UI? | `apps/desktop/src/sdk/index.ts:1887` exports `TRANSCRIPT_DIRECTIVE_AREA` | yes |
| Does WebApp load desktop plugins? | `hermes_cli/web_server_surface.py:44` serves `/api/desktop-plugins/*`; live `/api/desktop-plugins/list` returned 200 with this plugin | yes |
| Does core policy want capability at the edge? | Root `AGENTS.md`: "narrow waist; capability lives at the edges" | yes |
| Would a core `::ui` conflict? | Core already claims `preview`; this plugin claims `ui`. A built-in `ui` would shadow the plugin. | yes |

Therefore the plugin is the smallest surface that solves the problem. Core
changes are not required for this feature.

## What a core implementation would cost

A built-in `::ui` directive would need all of the following before merge:

1. A new TSX component under `apps/desktop/src/components/assistant-ui/`.
2. Registration in `apps/desktop/src/app/contrib/controller.tsx`.
3. A prompt-surface hint change plus the committed snapshot fixture under
   `tests/fixtures/prompt_surface/` (CI compares it).
4. Vitest behaviour-contract tests and an SDK type export.
5. Locale updates and a desktop design-system review.
6. A decision on precedence against a plugin that claims the same name.

That is a real cost on every user of core, while this plugin is opt-in and
hot-reloads. It is not justified yet.

## Reference only — NOT APPLIED

`docs/core-ui-reference.tsx` is a sketch of what step 1-2 would look like. It is
not imported, not compiled, and not part of this plugin's runtime. It exists so
a future PR can compare the two footprints without rediscovering the seam.

## Live verification performed

| Check | Result |
|---|---|
| `node --check` on `.mjs` copy | exit 0 |
| WebApp `/api/desktop-plugins/list` | HTTP 200, `intelligence-ui-abelion` present |
| `wizard` directive | `0 / 3`, three steps, Bantu/Sudah rendered as native DOM |
| `status` directive | `Hook / siap`, `Key / blocked` rows |
| `trace` directive | summary `Kenapa — 3 node` |
| `compare` directive | columns A1/A2 and B1/B2, `pick=right` outlined |
| `form` directive | 2 labelled inputs; submit sent `E2E form: Nama=Uji; Catatan=Catatan e2e` |
| Defect found and fixed | `form` initially rendered no inputs (forgot `children.push`); counter showed `0 / 0` on rowless cards |

Stacked directives on consecutive lines rendered as raw text; one-card-per-reply
is the supported contract until upstream #148562 lands.
