# Scope within generative UI

Aero is a bounded catalog: the assistant chooses one of eight card kinds and
supplies strings. The host parses the directive and the plugin renders native
React. It cannot generate arbitrary component trees, execute model JavaScript,
bind arbitrary tool outputs or negotiate a catalog with a foreign host.

The bundled skill is the generation guidance. It selects cards for ordinary
procedure/status/comparison/form requests, tells the model how to serialize
attributes, and separates native rendering from optional HTML preview. It is
not a model-training change or a guarantee of automatic live-model selection.

The renderer validates version/kind and bounds display/event values. The JSON
contract documents that behavior; it is not a runtime schema compiler. Actions
are short plain-text messages through the owning chat composer, not typed tool
calls or authorization tokens. Trace shows an observed work summary, never
private reasoning. There is no claim of compatibility with ChatGPT internals,
MCP Apps, AG-UI or an external generative-UI standard.

Future work, outside this PR: measured broad live-model selection reliability, schema-derived
prompts, typed events, data binding and incremental streaming patches. Keep
those claims separate from this opt-in eight-card plugin.
