# Title Reference — Internal Capability Tiers

Internal naming reference for plugins/modules/agents. Cosmic/Latin names carry natural hierarchy and function vibes. No external model-tier labels. This is the authority an agent uses to name a new plugin; do not invent a name outside these families without updating this file in the same PR.

## Registered plugins

Keep this list aligned with `hermes.json`. Each row states the stable id, the source folder, and the responsibility in one line.

| Plugin name | Id | Source | Responsibility |
|---|---|---|---|
| Nebula | `nebula` | `plugins/nebula/` | Privacy Guard: session-bound request/tool masking and held output redaction |

## Stellarium — full celestial reference

Stellarium is a **naming pool**, not a plugin and not limited to the Milky Way. It covers the whole observable sky: solar system bodies, stars, constellations, galaxies, and deep-sky objects. Use it when the plugin's job is observation, guidance, mapping, search, reference, or navigation. Pick a name from one family below and state the family in the PR rationale.

### Solar system — local, near, stateful
- **Sol** — sun; central/primary service, the thing others orbit
- **Luna** — moon; cache, mirror, reflected or derived state
- **Terra** — ground/home; baseline, origin, default profile
- **Mars**, **Venus**, **Mercury** — local anchors with distinct roles; use when the plugin set needs a consistent local family

### Centauri family — proximity and pairing
- **Alpha** — primary of a pair; main channel, primary host, first choice
- **Proxima** — nearest companion; fallback, sidecar, closest helper
- **Rigil** / **Toliman** — the two comparable members of a binary; use when neither is primary

### Stars — bright, specific, directional
- **Sirius** — brightest; high-visibility signal or status surface
- **Vega** — reference point/calibration; baselines and measurement
- **Polaris** — fixed direction; routing, navigation, stable anchors
- **Nova** — sudden burst; short-lived triggers, acceleration
- **Stella** — star (Latin); small collector, microservice

### Constellations — groups and structure
- **Orion** — recognizable group, multi-part toolset
- **Lyra** — compact, geometric, encoding-like work
- **Cygnus** — crossing paths, bridging, transport
- **Andromeda** — large neighboring structure; expansion or federation

### Deep sky — diffuse, large, slow
- **Nebula** — cloud of material; collectors, masking, transformation (already registered — see Registered plugins)
- **Galaxy** — large organized system; orchestration
- **Cosmos** — the whole scope; top-level core

## Other families (unchanged)

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

Match name to characteristic (speed, function, capacity, memory, scope). Adapt to module semantics; do not copy external tier labels. One plugin = one core word from a family above, no suffix. Keep the id stable across folder name, `plugin.yaml` `name`, and `hermes.json` `id`.

## Naming checklist for agents creating a plugin

Before opening the PR, confirm:

- [ ] Name is one core word from Stellarium, Elements, or Light & Time. No `-abelion`, no external model-tier suffix, no external model name.
- [ ] The family is named in "What changed" of the PR body.
- [ ] The id equals the folder name and `plugin.yaml` `name`, and matches the `hermes.json` entry.
- [ ] `docs/title-reference.md` registered-plugins table has a new row.
- [ ] The PR body uses `.github/PULL_REQUEST_TEMPLATE.md` unchanged, with all eight sections filled; "How it works" has one real image and "Verification" has command + result labels.
- [ ] The PR title is Conventional Commits, same form as the main commit.

The `pr-body-check` gate only checks that the eight sections have substantive text. The image in "How it works" and command + result labels in "Verification" are authoring requirements a reviewer checks, not CI-enforced checks.

## Visible name vs id

- Id (plugin.yaml `name`, hermes.json `id`, folder name): technical and stable. Never rename it for display.
- Visible name (what Hermes Desktop shows in Plugins): one core word from the families above, no suffix. The no-suffix limit applies to the visible name only, not to descriptions, PR titles or other text. Examples: Aero, Nebula, Proxima.
- Where the visible name comes from: plugin.yaml has no separate display-name field. A desktop entry is the object a plugin's `desktop/plugin.js` exports by default, shaped `{ id, name, register(ctx) }`. The Plugins page shows that entry's `name` (checked on Hermes Desktop v0.23.2). Set it there; leave plugin.yaml `name` as the id.
- A plugin with no desktop entry (Nebula has none in this repo): this reference does not say where its visible name comes from. Check the host before you claim one.
- The description may be technical. The visible name must not be.

## Example PR titles

Use Conventional Commits and the same form for the PR title (see `.github/PULL_REQUEST_TEMPLATE.md`).
- feat(aero): add bounded native transcript cards
- fix(nebula): mask credentials in held tool output
- docs(title-reference): add visible-name rule
- feat(proxima): add sidecar companion for Luna cache

## Images

- PR: one real image in "How it works" (see `.github/PULL_REQUEST_TEMPLATE.md`). For docs changes the template accepts a small accurate diagram of what changes.
- Plugin-produced images: not documented here. That means undocumented, not unsupported. State only what you verified and on which host version.
