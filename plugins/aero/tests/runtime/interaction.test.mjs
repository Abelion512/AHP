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
const result = await build({ stdin: { contents: source.replaceAll("'@hermes/plugin-sdk'", JSON.stringify(new URL('./sdk.mjs', import.meta.url).pathname)), resolveDir: process.cwd() }, bundle: true, write: false, format: 'esm', platform: 'node', external: ['react', 'react/jsx-runtime', new URL('./sdk.mjs', import.meta.url).pathname] })
const compiled = new URL('./.compiled-plugin.mjs', import.meta.url)
writeFileSync(compiled, result.outputFiles[0].text)
const plugin = (await import(compiled.href)).default
unlinkSync(compiled)

async function mounted(attrs, options = {}) {
  const stored = options.stored || new Map()
  let render
  const storage = { get: key => stored.get(key), set: (key,value) => stored.set(key,value) }
  plugin.register({ storage, register: c => { assert.equal(c.area, sdk.TRANSCRIPT_DIRECTIVE_AREA); render = c.data.render } })
  const node = document.createElement('div'); document.body.append(node)
  const root = createRoot(node)
  const props = { attrs: { version: '1', id: 'card', ...attrs }, streaming: false, sessionId: 'owner-chat', ...options.props }
  await act(async () => root.render(render(props)))
  return { node, stored, async update(next) { Object.assign(props,next); await act(async () => root.render(render(props))) }, async close() { await act(async () => root.unmount()); node.remove() } }
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
