import test from 'node:test'
import assert from 'node:assert/strict'
import {build} from 'esbuild'
import {writeFileSync,unlinkSync} from 'node:fs'
const dir=new URL('.',import.meta.url).pathname
const bundled=await build({entryPoints:[dir+'../../desktop/src/visual-card.mjs'],bundle:true,write:false,format:'esm',platform:'node',nodePaths:[dir+'node_modules']})
const compiled=new URL('./.compiled-photo.mjs',import.meta.url)
writeFileSync(compiled,bundled.outputFiles[0].text)
const {parseVisualCard,safeCardUrl,visualCardsRenderer}=await import(compiled.href)
unlinkSync(compiled)
import {product,attrsOf} from './photo-fixtures.mjs'
test('photo schema refuses incomplete or unsafe untrusted fields',()=>{
 const attrs=attrsOf(product)
 assert.equal(parseVisualCard(attrs).title,product.title)
 for(const url of ['http://example.com','javascript:alert(1)','https://127.0.0.1/a','https://user:pass@example.com/a','https://[::1]/a'])assert.equal(safeCardUrl(url),null)
 for(const extra of [{source:'javascript:alert(1)'},{extra:'unexpected'},{fact1:''},{price:'Rp1'},{pricenote:'Unknown'},{alt:'x'.repeat(121)}])assert.throws(()=>parseVisualCard({...attrs,...extra}))
 assert.equal(parseVisualCard({...attrs,price:'Unknown',pricenote:'Not checked'}).price,'Unknown')
})

test('photo groups remain alphabetical for shuffled attribute input',()=>{
 const b=attrsOf({...product,title:'Second'})
 const a=attrsOf({...product,title:'First'})
 const attrs=Object.fromEntries([...Object.entries(b).map(([k,v])=>['b_'+k,v]),...Object.entries(a).map(([k,v])=>['a_'+k,v])])
 const cards=visualCardsRenderer({attrs,streaming:false,sessionId:'test'}).props.children
 assert.deepEqual(cards.map(card=>card.props.data.title),['First','Second'])
})
