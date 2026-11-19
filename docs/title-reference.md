# Title Reference — Internal Capability Tiers

Internal naming reference for plugins/modules/agents. Cosmic/Latin names carry natural hierarchy and function vibes. No external model-tier labels.

## Our Plugin
- **Nebula** (`plugins/nebula/`) — Privacy Guard plugin; session-local PII/credential masking

## Tier Naming (our own, not external)
Pick names that match characteristic (speed, function, capacity, memory). Suggested sets:

### Cosmic & Scale
- Nebula / Stella — small collectors, microservices
- Nova — fast triggers, acceleration
- Galaxy / Cosmos — orchestrator, core

### Elements (function-based)
- Aqua — data flow, streaming, pipelines
- Ignis — execution, runtime, high-perf
- Aero — routing, UI, traffic
- Geo — storage, persistence, memory

### Light & Time (latency-based)
- Aurora — background processing
- Zenith — real-time priority
- Eclipse — security, fallback, isolation

## Usage Rule
Match name to characteristic. Adapt to module semantics; don't copy external tier labels.

## Visible name vs id
- Id (plugin.yaml `name`, hermes.json `id`, folder name): technical and stable. Never rename it for display.
- Visible name (what Hermes Desktop shows in Plugins): one core word from the tiers above, no suffix (this limit applies to the visible name only). Examples: Aero, Nebula.
- Where the visible name comes from: plugin.yaml has no separate display-name field. For a plugin with a desktop entry, the Plugins page shows that entry's `name` (checked on Hermes Desktop v0.23.2). Set it there; leave plugin.yaml `name` as the id.
- The description may be technical. The visible name must not be.

## Example PR titles
Use Conventional Commits and the same form for the PR title (see .github/PULL_REQUEST_TEMPLATE.md).
- feat(aero): add bounded native transcript cards
- fix(nebula): mask credentials in held tool output
- docs(title-reference): add visible-name rule

## Images
- PR: one real image in "How it works" (see .github/PULL_REQUEST_TEMPLATE.md). For docs changes the template accepts a small accurate diagram of what changes.
- Plugin-produced images: not documented here. That means undocumented, not unsupported. State only what you verified and on which host version.
