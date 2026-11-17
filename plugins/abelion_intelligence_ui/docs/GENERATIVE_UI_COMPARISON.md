# Generative UI landscape — sources, patterns, and where `::ui{...}` sits

Intelligent UI is not an OpenAI-only feature. It is the product-facing name for
a wider **generative UI** pattern: an agent selects or composes interface
elements at runtime, and the host renders them with components it owns.

## Sources used

| Source | What it gave | Evidence |
|---|---|---|
| [OpenUI — How ChatGPT Intelligent UI works](https://www.openui.com/blog/how-chatgpt-intelligent-ui-works) | Reverse-engineered DIL pipeline: model writes Markdown + JSX-like tags + JS; server compiles to JS program + JSON; sandboxed worker executes; native renderer applies operations | `TERVERIFIKASI` — article fetched, full text saved in session cache |
| [OpenUI — State of Generative UI 2026](https://www.openui.com/blog/state-of-generative-ui-report) | Separates **transport** (AG-UI vs MCP Apps) from **generation** (Static / Declarative / Open-Ended) | `TERVERIFIKASI` — search result with report text |
| [MCP Apps overview](https://apps.extensions.modelcontextprotocol.io/api/documents/overview.html) | `ui://` resources, sandboxed iframe, JSON-RPC over `postMessage`, host context, CSP | `TERVERIFIKASI` — spec page fetched earlier |
| [A2UI ecosystem](https://github.com/a2ui-project/a2ui/blob/main/docs/public/introduction/agent-ui-ecosystem.md) | Declarative JSON surfaces over AG-UI, catalog negotiation, non-web renderers | `TERVERIFIKASI` — search result |
| [assistant-ui](https://github.com/assistant-ui/assistant-ui) | `MessagePrimitive.GenerativeUI`, tool renderers, typed runtimes | `TERVERIFIKASI` — repo README fetched earlier |
| [CopilotKit guide 2026](https://www.copilotkit.ai/blog/the-developer-s-guide-to-generative-ui-in-2026) | Static / Declarative / Open-ended pattern names; AG-UI transport | `TERVERIFIKASI` — search result |
| [Ant Design X ThoughtChain](https://ant-design-x.antgroup.com/components/thought-chain) | Reasoning/thinking visual as collapsible status nodes with `loading/success/error/abort` | `TERVERIFIKASI` — docs page fetched |
| [ant-design/agentic-ui](https://github.com/antdigital-ai/agentic-ui) | ThoughtChainList, TaskList, ToolUseBar; process transparency | `TERVERIFIKASI` — repo README fetched |
| [affectUI — show what an agent is doing](https://www.affectui.com/guides/show-what-ai-agent-is-doing) | Current step → plan → tool calls → trace; "show what the agent is doing, not every token it thinks" | `TERVERIFIKASI` — article fetched |
| [ChatGPT share 6afc1e3d](https://chatgpt.com/share/6afc1e3d-bcd8-83ec-9f77-48edc630d5d6) | External AI critique of our directive: validation, state ownership, streaming, runtime separation | `PERKIRAAN` — another model's opinion, not a spec; extracted via `read_share.py` |

ChatGPT's own reply admitted OpenAI does not publish the full internal pipeline;
its DIL description relies on the OpenUI reverse engineering. So OpenUI is the
stronger technical source, while the ChatGPT share is only a critique.

## The two independent axes

| Axis | Options | Our position |
|---|---|---|
| Transport | AG-UI (own frontend) · MCP Apps (foreign hosts) · direct plugin SDK | Direct Hermes desktop-plugin SDK; we own the host, so no AG-UI/MCP needed |
| Generation | Static (select a prebuilt component) · Declarative (compose from catalog) · Open-ended (raw HTML/JS) | **Static-to-Declarative**: model selects one of five kinds and supplies capped props; it cannot compose arbitrary trees |

This is the same shape as tool-bound generative UI: a typed-ish function call
whose result is a UI. It is not OpenAI-specific and does not need a DIL-like
language.

## Pattern comparison

| Pattern | Wire format | Validation | Runtime | Strength | Cost |
|---|---|---|---|---|---|
| ChatGPT DIL | Markdown + JSX-like tags + JS | Server compiler + catalog schema | Sandboxed worker, native renderer | Rich local interaction, no model call per click | Compiler, sandbox, streaming patches, ops protocol |
| OpenUI Lang | Line-oriented `id = Component(args)` | Zod schemas; prompt derived from schema | React/Vue/Svelte/Native renderers | Compact, streamable, low token cost | Needs catalog + renderer |
| A2UI | JSON `createSurface` / `updateComponents` / `updateDataModel` | Catalog handshake | Flutter/Angular/Lit/React | Cross-platform, explicit data model | More tokens, more structure |
| json-render | JSON with Zod schemas | Schema validation | React/email/PDF/terminal | One spec, many targets | Higher token cost |
| MCP Apps | `ui://` HTML resource | CSP + sandbox | Sandboxed iframe in foreign host | Distribution into ChatGPT/Claude | Not native, resource predeclared |
| `::ui{...}` (ours) | One versioned line of `key="value"` attrs | Kind allowlist + caps + version check; JSON contract doc | Native React in Hermes transcript | Smallest surface, no core patch, no model JS | One card per reply; no arbitrary composition |

## Thinking / reasoning visual

OpenAI's Intelligent UI is about **answer** UI. The separate "thinking visual"
family answers a different question: what is the agent doing?

| Level | Question | Component pattern |
|---|---|---|
| Current step | Is it alive, and on what? | Thinking pill / one-line label with timer |
| Plan | How far along? | TaskList with done/current/upcoming |
| Tool calls | What did it call? | ToolUseBar / Tool Call Card, args folded |
| Multi-agent | Who is doing what? | Agent tree / lanes |
| Post-run | Where did time/cost go? | Trace waterfall |

Our `trace` kind is the smallest version of the first two levels: a collapsible
details node, three text nodes, evidence labels. It deliberately does **not**
show private chain-of-thought, matching affectUI's guidance: show what the
agent is doing, not every token it thinks.

## Gaps against the wider pattern

1. **Typed schema at runtime.** `directive-contract.json` documents the contract;
   the plugin enforces only caps, version, and kind allowlist. No typed AST.
2. **Catalog negotiation.** The model is not told the catalog through a schema;
   it learns kinds from the bundled skill text.
3. **Streaming patches.** We show a placeholder while `streaming` and render
   once; we do not stream partial components or preserve state across
   recompilation.
4. **Data binding.** No `updateDataModel` equivalent; tool results are not
   referenced by ID inside the card.
5. **Typed events.** `host.composer.submit` carries a plain string, not a
   schema-validated action/event object.
6. **Benchmarks.** No token-validity/cost measurement like the OpenUI report.

## Decisions

- Keep the plugin at the edge; do not build a mini-DIL or patch core.
- Keep static/declarative scope: five kinds, capped props, no model JS, no HTML.
- Next improvements, in order: runtime validator from the JSON contract,
  schema-derived prompt/catalog, typed event payloads, then streaming patches.
- `trace` stays a summary of observed work, never hidden reasoning replay.

## Verdict

`::ui{...}` is a small, model-agnostic instance of a common generative UI
pattern — closer to Static/tool-bound UI than to ChatGPT's full DIL compiler.
It is mature enough as an opt-in plugin, but it should not be described as a
general Intelligent UI standard. The general standard work is the catalogue,
schema, transport, and runtime layers documented above.
