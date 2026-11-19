# Intelligent UI reference observations

Observed 2026-11-18 on desktop. This is research and contributor material, not implementation acceptance. Existing Aero and OpenUI experiments remain separate. The manual contributor guide is [SKILL.md](../../.plugins/intelligent-ui-reference/SKILL.md); it is not registered with the runtime.

## Decision sequence

Imitate visual AND interaction behavior exactly, preserve the snapshot, prove stability in the full Hermes host, then modify only with approval. Favor simple and informative UI: few steps, clear controls, readable content and a visible return path, not feature count.

## Findings

| Family | Observed behavior | Scope and open gap |
| --- | --- | --- |
| ChatGPT Think products | Two peer columns with pale real-photo wells; title/price below; image opens image/source viewer. | Title click not tested. Model prices were not verified. |
| Gemini Hydrogen products | Generated a Canvas app with tall selectable cards, SVG board illustrations, detail and workload simulator. | Not real photos. More scrolling and navigation. Task-generated layout, not a native product standard. |
| ChatGPT places | Collage's map-looking image opens static image viewer. Separate inline map expands; pan moves roads/river/markers and reveals Search Here. Place opens place details; photo opens photo viewer. | Pannable map is distinct from static image. Dependency not approved under zero-billing constraint. |
| Gemini places | Existing natural Map Area/transit conversation has cards linked to place/map panel; pan works. | Two new Pi Store prompts gave prose only. Original model provenance unknown; current composer cannot establish historical mode. Photo enlargement not proven. |
| Charts, both | Synthetic Jan120, Feb95, Mar140, Apr110, May160, Jun130 kWh. Clicking Jan shows120kWh tooltip. | Gemini export not observed. ChatGPT also produced separate PNG with Expand, zoom, download, full-view and close controls; expand/close tested, download not tested. |
| DNS, both | Clickable steps, next/previous, quiz, wrong-red/right-green explanations and final score reached. | Gemini six stages/three questions/restart; ChatGPT eight stages/five questions/review. Content is generated per request, not a permanent native component. |
| ChatGPT video | Inline YouTube thumbnail/player; Play progressed from loading to title frame to board close-up. | Actual playback proven for one video, not arbitrary providers. |
| Gemini video | Initial prompt and followup returned text links rather than inline player. | Those runs only. Not a global capability claim. |

Provisional fit: ChatGPT native product/photo/video/PNG-viewer patterns are the simpler reference; Gemini's shorter DNS diagram is useful learning-flow evidence. This does not approve combining them into a new design. No Hermes code changed during this comparison.

## Provider feasibility

No new billing, keys, accounts or paid calls were activated. Maps Embed API usage is no-charge/unlimited but documented setup requires billing and an API key. Maps JavaScript has billing and PAYG; free monthly quotas do not meet a no-overage condition. Consumer Google Maps Share/Embed is separate and not verified as a dynamic-card implementation. OSM standard tiles are best effort with attribution/cache/referrer requirements and restrictions on prefetch/bulk/headless tile loading; no silent substitution is approved.

- https://developers.google.com/maps/documentation/embed/quickstart
- https://developers.google.com/maps/documentation/javascript/usage-and-billing
- https://developers.google.com/maps/billing-and-pricing/pricing
- https://support.google.com/maps/answer/7101463
- https://operations.osmfoundation.org/policies/tiles/

Prices/policies can change. Recheck final dependency conditions before implementation. Screenshots and private reference chats are intentionally not in this contributor package.

## Make product logs useful

Use [reference-case](templates/reference-case.md), [incident](templates/incident.md), [patch-plan](templates/patch-plan.md) and [verification](templates/verification.md). Record observations before explanations. A missing widget does not prove a platform cannot render it; a passing fixture does not prove full-host behavior. Never convert a hypothesis or incomplete check into a completed result.

### Initial sanitized regressions to protect

1. **Static image mistaken for map.** Cause established by clicking: an image opens image viewer. Fix in specification: separately identify the native map surface. Regression: drag must shift geographic geometry and markers together, not only move an image.
2. **Photo click replaced by custom detail.** Mismatch identified against reference: image target opens photo viewer, not unified detail. Required correction: preserve photo target and test it separately from title/place target. Implementation repair remains pending.
3. **Generated illustration mistaken for product photo.** SVG board drawing is not a real product photo. Regression: media provenance/type must match the request; label illustration or report photo unavailable.
4. **Spinner mistaken for successful playback.** Wait for changing frames after Play. Regression: player visible, play action, elapsed/frame progress, pause/error handling. One reference playback passed; Hermes player behavior remains untested.
5. **One quota notice generalized to all capabilities.** A chat-specific file/image restriction coexisted with a text-only video request accepted in another chat. Report exact blocked capability; never upgrade/switch accounts to avoid a limit.
6. **Free quota mistaken for zero-bill dependency.** Read billing prerequisites and overage conditions. Regression: no API-key/billing setup when net-zero cost cannot be guaranteed within the approved scope.

## Acceptance is still pending

The package does not assert the full Hermes implementation, fresh model requests, production safety or CI at any current PR head passed. Preserve and name those gaps until tested. No new PR, remote push, merge, deployment or dependency activation is included in this local documentation package.
