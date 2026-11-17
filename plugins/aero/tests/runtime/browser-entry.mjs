import React from 'react'
import { createRoot } from 'react-dom/client'
import plugin from '../../desktop/plugin.js'
import { segmentTranscriptDirectives } from '../../e2e/fixtures/transcript-directives.ts'
window.aeroAccept = true
window.aeroCalls = []
let render
plugin.register({storage:{get:key=>JSON.parse(localStorage.getItem(key)||'null'),set:(key,value)=>localStorage.setItem(key,JSON.stringify(value))},register:c=>{render=c.data.render}})
const examples = [
  '::ui{version="1" id="w" kind="wizard" title="Next steps" steps="Review evidence|Choose an option|Confirm action"}',
  '::ui{version="1" id="s" kind="status" title="Verification status" items="Unit tests:pass|Live host:not verified"}',
  '::ui{version="1" id="t" kind="trace" title="Observed work summary" steps="Read source|Test behavior|State limits"}',
  '::ui{version="1" id="c" kind="compare" title="Options" left="Native card|Text fallback" right="Sandbox preview|More setup" pick="left"}',
  '::ui{version="1" id="f" kind="form" title="Feedback" fields="Name|Notes" submit="Send feedback"}',
]
examples.push(
  '::ui{version="1" id="choices" kind="choice" title="Bagaimana lo mau belajar?" options="Lihat alurnya|Coba contoh|Bandingkan data" multiple="true"}',
  '::ui{version="1" id="flow" kind="flow" title="Dari pertanyaan ke visual" nodes="Pahami intent|Validasi data|Jelajahi visual" details="Model memilih bentuk yang membantu memahami pertanyaan|Renderer memeriksa jenis dan pasangan data sebelum menampilkan|Klik tahap atau grafik tanpa menunggu respons model baru"}',
  '::ui{version="1" id="chart" kind="chart" title="Contoh biaya tiga opsi" labels="Opsi A|Opsi B|Opsi C" values="12|8|20" unit="unit" source="Data ilustratif untuk tes, bukan harga produk"}',
)
const root=createRoot(document.getElementById('root'))
window.renderCards=(sessionId='owner-A',learningOnly=false)=>root.render(React.createElement('main',null,...examples.filter((_,i)=>!learningOnly||i>=5).map((text,index)=>{
  const parts=segmentTranscriptDirectives(text)
  const parsed=parts?.find(part=>part.kind==='directive')?.directive
  if (!parsed) throw Error('Pinned host parser failed to recognize fixture')
  return React.createElement('section',{'data-kind':parsed.attrs.kind,key:index},render({attrs:parsed.attrs,source:parsed.source,streaming:false,sessionId}))
})))
window.renderCards()
