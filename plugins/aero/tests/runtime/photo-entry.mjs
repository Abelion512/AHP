import React from 'react'
import {createRoot} from 'react-dom/client'
import plugin from '../../desktop/plugin.js'
import {segmentTranscriptDirectives} from '../../e2e/fixtures/transcript-directives.ts'
import {state} from './browser-sdk.mjs'
const renderers=new Map()
plugin.register({storage:{get:()=>null,set:()=>{}},register:c=>renderers.set(c.data.name,c.data.render)})
const root=createRoot(document.getElementById('root'))
window.aeroCalls=[];window.aeroAccept=true
window.photoRender=(raw,sessionId='owner-A',streaming=false)=>root.render(React.createElement('main',null,...raw.split(/\n\s*\n/).map((text,i)=>{
 const parsed=segmentTranscriptDirectives(text)?.find(p=>p.kind==='directive')?.directive
 return parsed?React.createElement('section',{key:i},renderers.get(parsed.name)({attrs:parsed.attrs,source:parsed.source,sessionId,streaming})):null
})))
let switchSequence=0
window.photoSwitch=()=>state.activeSessionId.set('rt-'+(++switchSequence))
