export const TRANSCRIPT_DIRECTIVE_AREA = 'transcript.directives'
function atom(value){const listeners=new Set();return{get:()=>value,listen:fn=>{listeners.add(fn);return()=>listeners.delete(fn)},set:next=>{if(next===value)return;value=next;listeners.forEach(fn=>fn(value))}}}
export const state={activeSessionId:atom('rt-A'),focusedSessionId:atom('rt-A'),focusedStoredSessionId:atom('owner-A'),connectionId:atom('test')}
export const host = {state, composer: { submit: (owner, text) => {
  if (!window.aeroAccept) return false
  window.aeroCalls.push({owner,text})
  return true
} } }
export function haptic() {}
