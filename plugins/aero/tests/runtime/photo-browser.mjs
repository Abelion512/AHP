import {build} from 'esbuild'
import {chromium} from '@playwright/test'
import {createServer} from 'node:http'
import {readFileSync} from 'node:fs'
import assert from 'node:assert/strict'
import {product,encode} from './photo-fixtures.mjs'
const dir=new URL('.',import.meta.url).pathname
const result=await build({entryPoints:[dir+'photo-entry.mjs'],bundle:true,write:false,format:'iife',platform:'browser',nodePaths:[dir+'node_modules'],alias:{'@hermes/plugin-sdk':dir+'browser-sdk.mjs'}})
const html='<!doctype html><meta name="viewport" content="width=device-width"><div id="root"></div><script>'+result.outputFiles[0].text+'</script>'
const server=createServer((q,r)=>{r.setHeader('content-type','text/html');r.end(html)})
await new Promise(r=>server.listen(0,'127.0.0.1',r))
const browser=await chromium.launch({headless:true,args:['--no-sandbox']})
const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message))
// Synthetic image bytes test the media controls, not product-photo provenance.
const syntheticImage={contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600"><rect width="800" height="600" fill="#cde"/><text x="30" y="50">SYNTHETIC TEST IMAGE</text></svg>'}
await page.route('https://assets.raspberrypi.com/**',r=>r.fulfill(syntheticImage))
// Fixtures use the stable product URL after the credential guard removed CDN cache keys.
await page.route('https://www.raspberrypi.com/products/raspberry-pi-5/',r=>r.fulfill(syntheticImage))
const raw=readFileSync(dir+'evidence/photo-response.md','utf8')
try{
 await page.goto('http://127.0.0.1:'+server.address().port)
 for(const width of [320,390,1280]){
  await page.setViewportSize({width,height:900});await page.evaluate(raw=>window.photoRender(raw),raw)
  await page.getByRole('article').nth(1).waitFor();assert.equal(await page.locator('.vc-price').count(),2)
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false)
  const trigger=page.getByRole('article').first().getByRole('button');await trigger.click()
  const modal=page.getByRole('dialog');await modal.waitFor()
  assert.equal(await modal.locator('h3,ul,.vc-summary,.vc-caveat').count(),0)
  assert.equal(await modal.getByRole('link').getAttribute('href'),product.source)
  assert.equal((await modal.getByRole('link').textContent()).includes('↗'),false)
  await modal.getByRole('combobox').selectOption('100');assert.equal(await modal.locator('.vc-stage').getAttribute('data-zoom'),'true')
  await page.keyboard.press('Escape');await modal.waitFor({state:'hidden'});assert.equal(await trigger.evaluate(e=>e===document.activeElement),true)
  await trigger.click();await modal.getByRole('button',{name:'Tutup',exact:true}).click();await modal.waitFor({state:'hidden'});assert.equal(await trigger.evaluate(e=>e===document.activeElement),true)
  await trigger.click();await page.evaluate(()=>window.photoSwitch());await modal.waitFor({state:'hidden'})
  assert.equal(await page.locator('dialog[open]').count(),0)
  await page.getByRole('region').click({position:{x:2,y:2}})
  await trigger.click();await page.evaluate(raw=>window.photoRender(raw,'owner-B'),raw);await page.waitForFunction(()=>!document.querySelector('dialog[open]'))
 }
 await page.evaluate(raw=>window.photoRender(raw,'owner-A',true),raw);await page.getByRole('status').first().waitFor();assert.equal(await page.getByRole('article').count(),0)
 await page.evaluate(raw=>window.photoRender(raw),`::visualcard{${encode({...product,source:'javascript:alert(1)'})}}`);await page.getByRole('alert').waitFor();assert.equal(await page.getByRole('article').count(),0)
 assert.equal(await page.evaluate(()=>window.aeroCalls.length),0);assert.deepEqual(errors,[])
 console.log(JSON.stringify({status:'PASS',checks:['paired price hierarchy','320/390/1280 no page overflow','photo/source-only dialog','zoom','Escape/X exact opener focus','SDK-state and owner-prop close','streaming hides controls','unsafe URL refusal','zero submits/page errors'],limits:['fake SDK atoms/composer','synthetic test image','pinned-parser harness, not full Hermes or model output']}))
}finally{await browser.close();server.close()}
