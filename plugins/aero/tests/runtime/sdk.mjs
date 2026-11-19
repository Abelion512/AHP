export const TRANSCRIPT_DIRECTIVE_AREA = 'transcript.directives'
export const calls = []
const atom = initial => { let value = initial; const listeners = new Set(); return { get: () => value, set: next => { value = next; listeners.forEach(fn => fn(next)) }, listen: fn => { listeners.add(fn); return () => listeners.delete(fn) } } }
export const host = {
  state: { activeSessionId: atom('owner-chat'), focusedSessionId: atom('wrong-focused-chat'), focusedStoredSessionId: atom('owner-chat'), connectionId: atom('test') },
  composer: { submit: (...args) => { calls.push(args); return true } },
}
export function haptic() {}
