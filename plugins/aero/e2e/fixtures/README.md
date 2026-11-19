# Pinned parser fixture

`transcript-directives.ts` is copied byte-for-byte from
`apps/desktop/src/lib/transcript-directives.ts` at Hermes core commit
`9a85916c87d56c2ca00b02fad8918f93ef1816e9`, the core commit already pinned
by repository CI. It is used without modification in the browser seam smoke.

Source: https://github.com/Abelion512/hermes-4gent/blob/9a85916c87d56c2ca00b02fad8918f93ef1816e9/apps/desktop/src/lib/transcript-directives.ts

The smoke uses the real parser, real React DOM and this plugin. Only the SDK
composer/storage/haptic bridge is fake. This is not a live user-host install,
a live provider/model evaluation, or a complete WebApp build.
