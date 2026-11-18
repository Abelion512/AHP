export const TRANSCRIPT_DIRECTIVE_AREA = 'transcript.directives'
export const calls = []
export const host = {
  state: { focusedSessionId: { get: () => 'wrong-focused-chat' } },
  composer: { submit: (...args) => { calls.push(args); return true } },
}
export function haptic() {}
