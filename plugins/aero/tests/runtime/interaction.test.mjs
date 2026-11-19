import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, writeFileSync, unlinkSync } from 'node:fs'
import { JSDOM } from 'jsdom'
import React, { act } from 'react'

import { build } from 'esbuild'

const dom = new JSDOM('<!doctype html><html><body></body></html>', { url: 'https://aero.invalid/' })
Object.assign(globalThis, { window: dom.window, document: dom.window.document, HTMLElement: dom.window.HTMLElement, IS_REACT_ACT_ENVIRONMENT: true })
const { createRoot } = await import('react-dom/client')
const source = readFileSync(new URL('../../desktop/plugin.js', import.meta.url), 'utf8')
// The same module instance is shared by plugin and test imports. No network or
// host account is involved; only the SDK bridge is replaced with an explicit fake.
const sdk = await import('./sdk.mjs')
const result = await build({ stdin: { contents: source.replaceAll("'@hermes/plugin-sdk'", JSON.stringify(new URL('./sdk.mjs', import.meta.url).pathname)), resolveDir: process.cwd() }, bundle: true, write: false, format: 'esm', platform: 'node', alias:{'@hermes/plugin-sdk':new URL('./sdk.mjs',import.meta.url).pathname}, external: ['react', 'react/jsx-runtime', new URL('./sdk.mjs', import.meta.url).pathname] })
const compiled = new URL('./.compiled-plugin.mjs', import.meta.url)
writeFileSync(compiled, result.outputFiles[0].text)
const { default: plugin, catalog, normalize } = await import(compiled.href)
unlinkSync(compiled)

async function mounted(attrs, options = {}) {
  const stored = options.stored || new Map()
  let render
  const storage = { get: key => stored.get(key), set: (key,value) => stored.set(key,value) }
  const renders = {}
  plugin.register({ storage, register: c => { assert.equal(c.area, sdk.TRANSCRIPT_DIRECTIVE_AREA); renders[c.data.name] = c.data.render } })
  render = renders[options.directive || 'ui']
  const node = document.createElement('div'); document.body.append(node)
  const root = createRoot(node)
  const props = { attrs: options.directive ? attrs : { version: '1', id: 'card', ...attrs }, streaming: false, sessionId: 'owner-chat', ...options.props }
  await act(async () => root.render(render(props)))
  return { node, stored, renders, async update(next) { Object.assign(props,next); await act(async () => root.render(render(props))) }, async close() { await act(async () => root.unmount()); node.remove() } }
}
async function click(node, label) {
  const button = [...node.querySelectorAll('button')].find(b => b.textContent === label)
  assert.ok(button, `missing button ${label}`)
  await act(async () => button.dispatchEvent(new window.MouseEvent('click', { bubbles:true })))
}

test('five kinds render actual DOM, not source strings', async () => {
  for (const [kind,attrs,expected] of [
    ['wizard',{steps:'First|Second'},'First'], ['status',{items:'Hook:siap|Key:blocked'},'blocked'],
    ['trace',{steps:'Input|Evidence'},'Kenapa - 2 node'], ['compare',{left:'A|B',right:'C|D'},'D'],
    ['form',{fields:'Name|Notes'},'Notes'],
  ]) {
    const card = await mounted({kind,...attrs}); assert.ok(card.node.textContent.includes(expected))
    if (kind !== 'wizard') assert.ok(!card.node.textContent.includes('0 /'))
    if (kind === 'form') assert.equal(card.node.querySelectorAll('input').length,2)
    await card.close()
  }
})
test('buttons route to card owner, never focused session', async () => {
  sdk.calls.length = 0
  const card = await mounted({kind:'wizard',title:'Task',steps:'First'})
  await click(card.node,'Bantu'); assert.deepEqual(sdk.calls,[['owner-chat','Bantu: Task - First']])
  await click(card.node,'Sudah'); assert.ok(card.node.textContent.includes('1 / 1'))
  await click(card.node,'Batal'); assert.ok(card.node.textContent.includes('0 / 1'))
  await card.close()
})
test('missing owner, composer refusal and thrown bridge fail closed', async () => {
  sdk.calls.length=0
  for (const owner of [undefined,null,'']) {
    const card=await mounted({steps:'First'}, {props:{sessionId:owner}})
    await click(card.node,'Bantu'); assert.equal(sdk.calls.length,0); assert.ok(card.node.querySelector('[role=alert]')); await card.close()
  }
  const submit=sdk.host.composer.submit
  for (const replacement of [()=>false,()=>{throw Error('unavailable')}]) {
    sdk.host.composer.submit=replacement
    const card=await mounted({steps:'First'}); await click(card.node,'Bantu'); assert.ok(card.node.querySelector('[role=alert]')); await card.close()
  }
  sdk.host.composer.submit=submit
})
test('progress persists by owner/card and follows labels after remount', async () => {
  const stored=new Map()
  const card=await mounted({steps:'First|Second'}, {stored})
  await click(card.node,'Sudah'); assert.ok(card.node.textContent.includes('1 / 2')); await card.close()
  const same=await mounted({steps:'Second|First'},{stored}); assert.ok(same.node.textContent.includes('1 / 2')); assert.equal(same.node.querySelectorAll('button')[3].textContent,'Batal'); await same.close()
  const other=await mounted({steps:'First|Second'},{stored,props:{sessionId:'other-chat'}}); assert.ok(other.node.textContent.includes('0 / 2')); await other.close()
})
test('changed card identity does not leak old progress or form state', async () => {
  const card=await mounted({steps:'First|Second'}); await click(card.node,'Sudah')
  await card.update({sessionId:'other-chat'}); assert.ok(card.node.textContent.includes('0 / 2'))
  await card.update({attrs:{version:'1',id:'new',kind:'wizard',steps:'New'}}); assert.ok(card.node.textContent.includes('0 / 1')); await card.close()
})
test('malformed saved state, unsupported version and streaming stay bounded', async () => {
  const key=JSON.stringify(['aero','1','owner-chat','card'])
  for (const saved of [[0,0,999],['First','First','x'],{},null]) {
    const card=await mounted({steps:'First'}, {stored:new Map([[key,saved]])}); assert.ok(!card.node.textContent.includes('2 / 1')); await card.close()
  }
  for (const attrs of [{version:'1evil'},{kind:'unknown'}]) { const card=await mounted(attrs); assert.ok(card.node.textContent.includes('tidak didukung')); assert.equal(card.node.querySelectorAll('button').length,0); await card.close() }
  const live=await mounted({steps:'First'},{props:{streaming:true}}); assert.equal(live.node.querySelectorAll('button').length,0); await live.update({streaming:false}); assert.equal(live.node.querySelectorAll('button').length,2); await live.close()
})
test('untrusted text is text, rows capped, oversized form never truncates silently', async () => {
  const card=await mounted({title:'<img src=x onerror=alert(1)>',steps:Array(20).fill('x'.repeat(1000)).join('|')})
  assert.equal(card.node.querySelectorAll('img,script').length,0); assert.equal(card.node.querySelectorAll('button').length,16); assert.ok(card.node.textContent.length<1000); await card.close()
  sdk.calls.length=0
  const form=await mounted({kind:'form',title:'T',fields:'A|B'})
  const inputs=form.node.querySelectorAll('input')
  const set=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set
  await act(async()=> { set.call(inputs[0],'one'); inputs[0].dispatchEvent(new window.Event('input',{bubbles:true})); set.call(inputs[1],'two'); inputs[1].dispatchEvent(new window.Event('input',{bubbles:true})) })
  await click(form.node,'Kirim'); assert.deepEqual(sdk.calls[0],['owner-chat','T: A=one; B=two'])
  sdk.calls.length=0
  await act(async()=> { for (const input of inputs) { set.call(input,'x'.repeat(160)); input.dispatchEvent(new window.Event('input',{bubbles:true})) } })
  await click(form.node,'Kirim'); assert.equal(sdk.calls.length,0); assert.ok(form.node.querySelector('[role=alert]').textContent.includes('240')); await form.close()
})

async function inputText(input, value) {
  const set = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set
  await act(async () => { set.call(input, value); input.dispatchEvent(new window.Event('input', { bubbles: true })) })
}

test('choice: local selection does not send; explicit submit preserves owner and note', async () => {
  sdk.calls.length = 0
  const card = await mounted({ kind: 'choice', title: 'Belajar', options: 'Diagram|Contoh|Teks', multiple: 'true' })
  assert.equal(card.node.querySelector('button').disabled, true)
  await act(async () => card.node.querySelectorAll('input')[0].click())
  await act(async () => card.node.querySelectorAll('input')[1].click())
  assert.equal(sdk.calls.length, 0)
  await inputText(card.node.querySelector('input[type=text]'), 'Singkat')
  await click(card.node, 'Kirim jawaban')
  assert.deepEqual(sdk.calls, [['owner-chat', 'Jawaban: Belajar - Diagram; Contoh; Catatan: Singkat']])
  await card.update({ sessionId: 'other-owner' })
  assert.equal(card.node.querySelectorAll('input:checked').length, 0)
  assert.equal(card.node.querySelector('input[type=text]').value, '')
  await card.close()
})

test('single-choice cards isolate radio groups; missing owner and overflow refuse sends', async () => {
  sdk.calls.length = 0
  const a = await mounted({ kind: 'choice', title: 'A', options: 'Satu|Dua' })
  const b = await mounted({ kind: 'choice', title: 'B', options: 'Satu|Dua' })
  await act(async () => a.node.querySelector('input').click())
  await act(async () => b.node.querySelector('input').click())
  assert.equal(a.node.querySelector('input').checked, true)
  await act(async () => a.node.querySelectorAll('input')[1].click())
  assert.equal(a.node.querySelectorAll('input:checked').length, 1)
  assert.equal(a.node.querySelectorAll('input')[1].checked, true)
  await a.close(); await b.close()
  const noOwner = await mounted({ kind: 'choice', options: 'Satu|Dua' }, { props: { sessionId: null } })
  await act(async () => noOwner.node.querySelector('input').click())
  assert.equal(noOwner.node.querySelector('button').disabled, true); await noOwner.close()
  const big = await mounted({ kind: 'choice', title: 'T'.repeat(80), options: ['A', 'B', 'C'].map(c => c.repeat(60)).join('|'), multiple: 'true' })
  for (const input of big.node.querySelectorAll('input[type=checkbox]')) await act(async () => input.click())
  await click(big.node, 'Kirim jawaban')
  assert.equal(sdk.calls.length, 0); assert.ok(big.node.querySelector('[role=alert]').textContent.includes('240'))
  await big.close()
})

test('flow exploration and chart focus/table are local, truthful numeric views', async () => {
  sdk.calls.length = 0
  const flow = await mounted({ kind: 'flow', title: 'Permintaan', nodes: 'Model|Validator|Renderer', details: 'Pilih komponen|Periksa data|Gambar UI' })
  assert.ok(flow.node.textContent.includes('Pilih komponen'))
  await click(flow.node, '2. Validator')
  assert.ok(flow.node.textContent.includes('Periksa data'))
  assert.ok(!flow.node.textContent.includes('Pilih komponen'))
  assert.equal(flow.node.querySelector('button[aria-pressed=true]').textContent, '2. Validator')
  await flow.close()
  const chart = await mounted({ kind: 'chart', title: 'Waktu contoh', labels: 'Teks|Visual|Campuran', values: '10|0|5', unit: 'menit', source: 'Contoh ilustratif, bukan pengukuran' })
  assert.ok(chart.node.textContent.includes('10 menit'))
  assert.ok(chart.node.textContent.includes('Contoh ilustratif'))
  await click(chart.node, 'Tabel data')
  assert.equal(chart.node.querySelectorAll('tbody tr').length, 3)
  assert.equal(chart.node.querySelectorAll('tbody td')[1].textContent, '0')
  await click(chart.node, 'Tutup tabel data')
  assert.equal(chart.node.querySelector('table'), null)
  assert.equal(sdk.calls.length, 0)
  await chart.close()
})

test('table kind renders a headered data table locally with bounded data', async () => {
  sdk.calls.length = 0
  const card = await mounted({ kind: 'table', title: 'Laptop', columns: 'Merk|Harga|Sumber', rows: 'Asus;Rp 8 jt;plazait.com|Lenovo;Rp 9 jt;erablue.id' })
  assert.equal(card.node.querySelectorAll('thead th').length, 3)
  assert.equal(card.node.querySelectorAll('tbody tr').length, 2)
  assert.ok(card.node.textContent.includes('plazait.com'))
  assert.equal(sdk.calls.length, 0)
  await card.close()
  for (const attrs of [
    { kind: 'table', columns: 'A|B' },
    { kind: 'table', columns: 'A|B', rows: 'x;y|z' },
    { kind: 'table', columns: 'A', rows: 'x|'.repeat(9) + 'x' },
  ]) {
    const bad = await mounted(attrs)
    assert.ok(bad.node.querySelector('[role=status]'), JSON.stringify(attrs))
    assert.equal(bad.node.querySelector('table'), null)
    await bad.close()
  }
})

test('map kind renders renderer-built static OSM tiles with labeled pins', async () => {
  sdk.calls.length = 0
  const card = await mounted({ kind: 'map', title: 'Tempat', places: 'Monas;-6.1754;106.8272;Ikon|Kota Tua;-6.1352;106.8133' })
  const imgs = [...card.node.querySelectorAll('img')]
  assert.equal(imgs.length, 9)
  assert.ok(imgs.every(i => i.src.startsWith('https://tile.openstreetmap.org/')), imgs.map(i => i.src).join(','))
  assert.ok(card.node.textContent.includes('Monas'))
  assert.ok(card.node.textContent.includes('Kota Tua'))
  assert.ok(card.node.textContent.includes('OpenStreetMap contributors'))
  assert.ok(card.node.textContent.includes('Peta statis'))
  assert.equal(sdk.calls.length, 0)
  await card.close()
  for (const attrs of [
    { kind: 'map', places: 'Monas;-6.17' },
    { kind: 'map', places: 'Monas;999;106.82' },
    { kind: 'map', places: 'Monas;abc;106.82' },
    { kind: 'map', places: Array(6).fill('X;-6.1;106.8').join('|') },
    { kind: 'map', places: '' },
  ]) {
    const bad = await mounted(attrs)
    assert.ok(bad.node.querySelector('[role=status]'), JSON.stringify(attrs))
    assert.equal(bad.node.querySelector('img'), null)
    await bad.close()
  }
})

test('data-rich cards reject malformed types, pairings and nonfinite/negative numbers', async () => {
  for (const attrs of [
    { kind: 'choice', options: 'Only' }, { kind: 'choice', options: 'Same|Same' },
    { kind: 'choice', options: 'A|B', multiple: 'yes' },
    { kind: 'flow', nodes: 'A|B', details: 'One' },
    { kind: 'flow', nodes: 'A|B', details: 'x'.repeat(181) + '|Two' },
    ...['NaN', 'Infinity', '-1', '1e4', '1;alert(1)', '', '9999999999'].map(value => ({ kind: 'chart', labels: 'A', values: value })),
    { kind: 'chart', labels: 'A|B', values: '1' },
    { kind: 'choice', options: Array(7).fill('x').join('|') },
  ]) {
    const card = await mounted(attrs)
    assert.ok(card.node.querySelector('[role=status]'), JSON.stringify(attrs))
    assert.equal(card.node.querySelectorAll('button,input').length, 0)
    await card.close()
  }
})

test('published catalog, contract and model examples agree', () => {
  const contract = JSON.parse(readFileSync(new URL('../../docs/directive-contract.json', import.meta.url)))
  const skill = readFileSync(new URL('../../skills/aero/SKILL.md', import.meta.url), 'utf8')
  assert.deepEqual(Object.keys(catalog).sort(), Object.keys(contract.kinds).sort())
  for (const kind of Object.keys(catalog)) assert.ok(skill.includes('| ' + kind + ' |'))
  assert.equal(Object.isFrozen(catalog), true)
  for (const kind of ['choice', 'flow', 'chart', 'interview', 'quiz', 'table', 'map']) {
    const line = skill.split('\n').find(s => s.startsWith('::ui{') && s.includes('kind="' + kind + '"'))
    assert.ok(line, kind)
    const attrs = Object.fromEntries([...line.matchAll(/(\w+)="([^"]*)"/g)].map(m => [m[1], m[2]]))
    assert.equal(normalize(attrs).error, undefined)
    assert.ok(line.slice(5, -1).length <= 2048)
  }
})

test('fractional and zero charts have truthful bar scales and local state resets', async () => {
  for (const [values, widths] of [['0.2|0.4', ['50%', '100%']], ['0|0', ['0%', '0%']]]) {
    const card = await mounted({ kind: 'chart', labels: 'A|B', values })
    assert.deepEqual([...card.node.querySelectorAll('[aria-hidden=true]>span')].map(n => n.style.width), widths)
    await click(card.node, 'Tabel data')
    await card.update({ sessionId: 'other' })
    assert.equal(card.node.querySelector('table'), null)
    await card.close()
  }
  const flow = await mounted({ kind: 'flow', nodes: 'A|B', details: 'First|Second' })
  await click(flow.node, '2. B')
  await flow.update({ attrs: { version: '1', id: 'other', kind: 'flow', nodes: 'C|D', details: 'Third|Fourth' } })
  assert.equal(flow.node.querySelector('[aria-pressed=true]').textContent, '1. C')
  await flow.close()
})

const interviewAttrs = { kind: 'interview', title: 'Review', groups: 'Scope|Trigger', g1_options: 'Verify::Status only|Merge::After approval', g2_options: 'Webhook::On change|Manual', submit: 'Save decision' }
async function pickRadio(node, group, index) {
  const input = node.querySelectorAll(`input[name$="-${group}"]`)[index]
  assert.ok(input, `missing radio ${group}/${index}`)
  await act(async () => input.dispatchEvent(new window.MouseEvent('click', { bubbles: true })))
}
test('interview needs every group, then sends one owner-routed answer', async () => {
  sdk.calls.length = 0
  const card = await mounted(interviewAttrs)
  const save = () => [...card.node.querySelectorAll('button')].find(b => b.textContent === 'Save decision')
  assert.equal(save().disabled, true)
  await pickRadio(card.node, 0, 1)
  assert.equal(save().disabled, true)
  await pickRadio(card.node, 1, 0)
  assert.equal(save().disabled, false)
  await click(card.node, 'Save decision')
  assert.deepEqual(sdk.calls, [['owner-chat', 'Jawaban: Review - Scope: Merge; Trigger: Webhook']])
  await card.close()
  const orphan = await mounted(interviewAttrs, { props: { sessionId: '' } })
  assert.equal([...orphan.node.querySelectorAll('button')].find(b => b.textContent === 'Save decision').disabled, true)
  await orphan.close()
})
test('interview and quiz reject malformed or oversized data without rendering it', async () => {
  for (const attrs of [
    { ...interviewAttrs, groups: 'A|B|C|D|E' },
    { ...interviewAttrs, g1_options: 'Only one' },
    { ...interviewAttrs, g2_options: 'Same|Same' },
    { ...interviewAttrs, g1_options: 'X::' + 'y'.repeat(181) + '|Other' },
    { kind: 'quiz', questions: 'Q', q1_options: 'A|B', q1_answer: 'C' },
    { kind: 'quiz', questions: 'Q', q1_options: 'A|B' },
    { kind: 'quiz', questions: 'Q', q1_options: 'A|A', q1_answer: 'A' },
    { kind: 'quiz', questions: 'Q1|Q2|Q3|Q4|Q5|Q6', q1_options: 'A|B', q1_answer: 'A' },
  ]) assert.ok(normalize(attrs).error, JSON.stringify(attrs).slice(0, 60))
  const card = await mounted({ ...interviewAttrs, g1_options: '<img src=x onerror=alert(1)>::<b>x</b>|Other' })
  assert.equal(card.node.querySelector('img,b'), null)
  assert.ok(card.node.textContent.includes('<img src=x'))
  await card.close()
})
test('quiz marks correct and wrong, gates Next, scores locally and never messages the chat', async () => {
  sdk.calls.length = 0
  const card = await mounted({ kind: 'quiz', title: 'Quiz', questions: 'First?|Second?', q1_options: 'A1|B1|C1', q1_answer: 'B', q1_explain: 'Because B.', q2_options: 'A2|B2', q2_answer: 'A' })
  const next = () => [...card.node.querySelectorAll('.aero-quiz-next')][0]
  assert.equal(next().disabled, true)
  assert.ok(card.node.textContent.includes('Soal 1 dari 2'))
  await click(card.node, 'AA1')
  const states = [...card.node.querySelectorAll('.aero-quiz-opt')].map(b => b.dataset.state)
  assert.deepEqual(states, ['wrong', 'correct', 'idle'])
  assert.ok(card.node.textContent.includes('Because B.'))
  assert.equal(next().disabled, false)
  await act(async () => next().dispatchEvent(new window.MouseEvent('click', { bubbles: true })))
  await click(card.node, 'AA2')
  await act(async () => next().dispatchEvent(new window.MouseEvent('click', { bubbles: true })))
  assert.ok(card.node.textContent.includes('Skor 1 dari 2'))
  assert.deepEqual(sdk.calls, [])
  await card.close()
})

test('visual card separates image viewer, product detail and labeled source button', async () => {
  const { product, attrsOf } = await import('./photo-fixtures.mjs')
  if (!window.HTMLDialogElement.prototype.showModal) {
    window.HTMLDialogElement.prototype.showModal = function () { this.setAttribute('open', '') }
    window.HTMLDialogElement.prototype.close = function () { this.removeAttribute('open') }
  }
  const card = await mounted(attrsOf(product), { directive: 'visualcard' })
  const img = card.node.querySelector('button.vc-image')
  const title = card.node.querySelector('button.vc-title')
  assert.equal(img.getAttribute('aria-label'), 'Perbesar gambar ' + product.title)
  assert.equal(title.getAttribute('aria-label'), 'Detail ' + product.title)
  const link = card.node.querySelector('a.vc-source.vc-button')
  assert.equal(link.textContent, 'Lihat produk')
  assert.equal(link.getAttribute('href'), product.source)
  assert.equal(link.getAttribute('rel'), 'noopener noreferrer')
  assert.equal(link.getAttribute('target'), '_blank')
  const viewer = card.node.querySelector('dialog.vc-viewer')
  const detail = card.node.querySelector('dialog.vc-detail')
  assert.ok(viewer && detail)
  // Image click opens only the viewer; title click opens only the detail; body text click opens detail.
  await act(async () => img.dispatchEvent(new window.MouseEvent('click', { bubbles: true })))
  assert.ok(viewer.hasAttribute('open')); assert.ok(!detail.hasAttribute('open'))
  await act(async () => viewer.close())
  await act(async () => title.dispatchEvent(new window.MouseEvent('click', { bubbles: true })))
  assert.ok(detail.hasAttribute('open')); assert.ok(!viewer.hasAttribute('open'))
  await act(async () => detail.close())
  await act(async () => card.node.querySelector('.vc-summary').dispatchEvent(new window.MouseEvent('click', { bubbles: true })))
  assert.ok(detail.hasAttribute('open')); assert.ok(!viewer.hasAttribute('open'))
  await act(async () => detail.close())
  await card.close()
  const place = await mounted(attrsOf({ ...product, kind: 'place' }), { directive: 'visualcard' })
  assert.equal(place.node.querySelector('a.vc-source.vc-button').textContent, 'Buka sumber')
  await place.close()
})
