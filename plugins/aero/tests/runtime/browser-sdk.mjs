export const TRANSCRIPT_DIRECTIVE_AREA = 'transcript.directives'
export const host = { composer: { submit: (owner, text) => {
  if (!window.aeroAccept) return false
  window.aeroCalls.push({owner,text})
  return true
} } }
export function haptic() {}
