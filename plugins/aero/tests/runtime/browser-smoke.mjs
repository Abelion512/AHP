import { build } from 'esbuild'
import { chromium } from '@playwright/test'
import { createServer } from 'node:http'
import { mkdirSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'
import assert from 'node:assert/strict'
const dir=new URL('.',import.meta.url).pathname
const output=process.env.AERO_ARTIFACTS || resolve(dir,'artifacts')
mkdirSync(output,{recursive:true})
const result=await build({entryPoints:[dir+'browser-entry.mjs'],bundle:true,write:false,format:'iife',platform:'browser',nodePaths:[dir+'node_modules'],alias:{'@hermes/plugin-sdk':dir+'browser-sdk.mjs'}})
const html='<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><style>:root{--foreground:#132136;--muted-foreground:#54657b;--accent:#2461b4;--border:#d8e1eb}*{box-sizing:border-box}body{margin:0;background:#f3f6fa;font-family:Arial,sans-serif}main{max-width:860px;margin:24px auto;padding:0 16px}section{background:white;border:1px solid var(--border);border-radius:12px;padding:14px 18px;margin:14px 0}h1{font-size:24px}</style><div id="root"></div><script>'+result.outputFiles[0].text+'</script>'
const server=createServer((req,res)=>{res.setHeader('content-type','text/html');res.end(html)})
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve))
const browser=await chromium.launch({headless:true,args:['--no-sandbox']})
try {
 const page=await browser.newPage({viewport:{width:1100,height:950}})
 const errors=[];page.on('pageerror',err=>errors.push(err.message))
 await page.goto('http://127.0.0.1:'+server.address().port)
 await page.getByText('Next steps',{exact:true}).waitFor()
 assert.equal(await page.locator('section').count(),5)
 assert.equal(await page.locator('iframe').count(),0)
 await page.getByRole('button',{name:'Sudah',exact:true}).first().click()
 await page.getByText('1 / 3',{exact:true}).waitFor()
 await page.getByRole('button',{name:'Bantu',exact:true}).first().click()
 assert.deepEqual(await page.evaluate(()=>window.aeroCalls),[{owner:'owner-A',text:'Bantu: Next steps - Review evidence'}])
 await page.getByLabel('Name',{exact:true}).fill('Test')
 await page.getByLabel('Notes',{exact:true}).fill('Browser interaction')
 await page.getByRole('button',{name:'Send feedback',exact:true}).click()
 assert.deepEqual((await page.evaluate(()=>window.aeroCalls)).at(-1),{owner:'owner-A',text:'Feedback: Name=Test; Notes=Browser interaction'})
 await page.reload();await page.getByText('1 / 3',{exact:true}).waitFor()
 await page.evaluate(()=>window.renderCards('owner-B'));await page.getByText('0 / 3',{exact:true}).waitFor()
 await page.getByRole('button',{name:'Bantu',exact:true}).first().click()
 assert.equal((await page.evaluate(()=>window.aeroCalls)).at(-1).owner,'owner-B')
 await page.evaluate(()=>window.aeroAccept=false)
 await page.getByRole('button',{name:'Bantu',exact:true}).first().click()
 await page.getByRole('alert').waitFor()
 await page.evaluate(()=>{window.aeroAccept=true;window.renderCards('owner-A')})
 await page.getByText('1 / 3',{exact:true}).waitFor()
 await page.getByText('Kenapa - 3 node',{exact:true}).click()
 await page.screenshot({path:output+'/aero-desktop.png',fullPage:true})
 await page.setViewportSize({width:390,height:844})
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false)
 await page.screenshot({path:output+'/aero-mobile.png',fullPage:true})
 assert.deepEqual(errors,[])
 const report={status:'PASS',cards:5,host_parser:'9a85916c87d56c2ca00b02fad8918f93ef1816e9',checks:['native DOM for all5kinds','wizard toggle','owning-session send','form values','reload persistence','cross-owner isolation','composer refusal','trace expansion','390px no horizontal overflow'],limits:['fake SDK composer/storage bridge','not a live user-host install','not a live model generation test']}
 writeFileSync(output+'/report.json',JSON.stringify(report,null,2))
 console.log(JSON.stringify(report))
} finally {await browser.close();server.close()}
