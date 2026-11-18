---
name: intelligent-ui-reference
description: Contribute a reference-faithful Intelligent UI patch and record interaction evidence.
---

# Intelligent UI reference contribution

Manual contributor guide, not a registered Hermes plugin skill or a new runtime feature.
Read the repository's contribution rules and the relevant plugin's README, USAGE and skills before changing code. Use the repository's PR template and current test/label rules.

## Scope

Use `experiments/intelligent-ui-reference/README.md` for the observed comparison and limits. Start from an approved reference family, not a new hybrid. Preserve Aero and existing experimental snapshots. Never change another PR's scope, merge, deploy, enable billing or add accounts as part of a visual patch.

## Procedure

1. Record the prompt, exact selected model/mode, viewport, initial state, reference date and public source. Use a sanitized screenshot; keep private conversation links outside the repo.
2. Click the reference. Record where image, title, map, Expand, close, next and back each lead. A screenshot alone cannot prove an interaction. Distinguish fixed native UI from a one-off generated app.
3. Write a small acceptance contract before implementation: same visual grouping, action targets, state changes and return path. List every unverified action. Do not fill gaps with an invented detail panel.
4. Preserve the imitation snapshot before modification. Label adaptations separately, and request approval before changing a reference behavior.
5. Run unit/component tests, then build and exercise the real Hermes host. New unseen requests must traverse the selected real model and renderer, not only fixtures or a mocked composer. Do not silently change provider/model if a quota blocks the run.
6. Test 320/390/1280 widths, dark/light as supported, keyboard/focus, empty/error/loading, owner/session change and interrupted/duplicate submission. Assert network destinations, hostile markup/URLs, action ownership and failure visibility.
7. Convert each failure into a sanitized incident with evidence, a proven cause or explicitly marked hypothesis, a narrow fix and a regression test. Review the exact final commit's required jobs, including absent jobs. Green returned jobs alone do not prove full coverage.
8. Prepare the PR with baseline/head, changed behavior, before/after screenshots, reproducible commands, positive/negative results, unverified cases, costs, rollback and limitations. Human owner retains merge/deploy decisions.

## Money and dependencies

Current project constraint: net Rp0, no PAYG and no billing activation. A free quota with an overage rate is not zero-cost proof. Maps Embed API documentation still requires billing/key despite free usage. Consumer Share/Embed is a separate feature, not proof of an automated dynamic-map dependency. Do not silently substitute OSM: tile use has attribution, caching and traffic conditions and no SLA.

## Reporting

Use the templates in `experiments/intelligent-ui-reference/templates/`. Claims must say which layer passed: component, simulated integration, full host, real model or deployed. A local test is not a live deployment. Never commit private chat exports, account identifiers, credentials, internal logs or personal information. Product events can inform improvements after sanitization; raw logs are not automatically contribution material.
