# Aero

Eight native visual and interactive cards in the Hermes Desktop/WebApp transcript. The
bundled Aero skill teaches the assistant to choose a card from ordinary requests;
the user does not need to type directive syntax. No iframe or core patch.

## Install, without changing a running profile automatically

Aero has two halves. Install the plugin package with the host's normal plugin
management so `skills/aero/SKILL.md` is discoverable. The existing repository
updater syncs Nebula only; it does not install Aero. For the native renderer,
link this package's `desktop/` directory into the intended profile's
`desktop-plugins/aero` directory, then reload that host. For a default profile,
from this package directory:

```sh
mkdir -p "$HOME/.hermes/desktop-plugins"
ln -s "$PWD/desktop" "$HOME/.hermes/desktop-plugins/aero"
```

Do not overwrite an existing link. For a non-default profile, use that profile's
home rather than assuming `~/.hermes`. Confirm Aero is enabled and the skill is
loaded in a new session, then confirm a directive renders as a card. A 200 file
response alone is not proof. This PR does not install or activate a user's host.

Supported SDK contract: `TranscriptDirectiveProps.sessionId` and
`host.composer.submit(sessionId, text): boolean`, as pinned by repository CI to
core `9a85916c87d56c2ca00b02fad8918f93ef1816e9`. Missing owner refuses sends;
it never falls back to the focused chat. Older hosts can display cards but may
lack the safe action bridge. No claim of universal older-host compatibility.

## Directive catalog

Author a complete directive on one line outside code fences. The pinned parser
also supports inline/stacked directives; a separate line is our readable
convention, not a parser restriction.

| kind | attributes | result |
|---|---|---|
| wizard | title, steps="A\|B\|C" | numbered steps, local progress, Bantu/Sudah |
| status | title, items="Label:state\|..." | rows with a state dot |
| trace | title, steps="Read source\|Test behavior" | collapsible observed-work summary |
| compare | title, left="A\|B", right="C\|D", pick="left" | two columns |
| form | title, fields="Name\|Notes", submit="Send" | short non-secret inputs |
| choice | title, options="A\|B", multiple="true" | single/multi-choice, optional note, explicit submit |
| flow | title, nodes="A\|B", details="Why A\|Why B" | clickable visual sequence and local explanation |
| chart | title, labels="A\|B", values="12\|8", unit, source | proportional bars, focus and equivalent table |

```text
::ui{version="1" id="review-01" kind="wizard" title="Next steps" steps="Review evidence|Choose an option|Confirm"}
```

Use explicit unique ids. Only wizard completion labels persist, scoped by owning
chat and card id. No explicit id means no persistence. Form/choice values and flow/chart exploration stay in memory
and reset when owner/card attributes change. Missing/wrong version or kind has a
visible safe fallback. Streaming cards have no action controls.

Untrusted strings render as text, never HTML. Unknown attributes are ignored.
Titles cap at 80 characters, rows at 8 x 60, comparison rows and fields at 6,
field values at 160. The host parser caps the body at 2048. Full action messages
over 240 characters are refused visibly, never silently truncated. Composer
acceptance is not proof that a model completed the requested action. Local
wizard toggles are not proof that the underlying work happened. No direct
network, secrets, arbitrary JS or general UI tree language. New data-rich kinds
normalize into a validated typed record before rendering; actions still use
the existing short text composer bridge, not a typed host event API.

## Verification

```sh
python3 -m unittest discover -s plugins/aero/tests -v
cd plugins/aero/tests/runtime
npm ci
npm test
npx playwright install --with-deps chromium
npm run test:browser
```

The locked React suite covers state, negative controls and exact action payloads.
The Chromium smoke uses the unmodified pinned host parser, real React DOM and
Aero, with a fake SDK bridge. It exercises all eight kinds, form edits, owner
routing, refusal, reload persistence, owner isolation, trace expansion and 390px
overflow, and emits screenshots/report. See `docs/VERIFICATION.md` for scope and
`e2e/README.md` for the optional live-host smoke, which creates a real session.
A deterministic parser/renderer pass is not a live provider's autonomous skill
selection test. The earlier five-kind baseline has a bounded live wizard smoke. New choice/flow/chart
kinds are deterministic-only until a separately authorized live smoke is run.

## Visual-learning design

See [DESIGN.md](docs/DESIGN.md) for the original references, choice of safe
components over a second chat shell, learning-oriented criteria and limits.
The chart uses paired nonnegative values; unknown data is not a zero. Flow is an
ordered sequence, not an arbitrary graph. Exploration stays local until an
explicit choice submit. A picture alone is not evidence of better comprehension.
