import test from 'node:test'
import assert from 'node:assert/strict'
import {build} from 'esbuild'
import {writeFileSync,unlinkSync} from 'node:fs'
const dir=new URL('.',import.meta.url).pathname
const bundled=await build({entryPoints:[dir+'../../desktop/src/visual-card.mjs'],bundle:true,write:false,format:'esm',platform:'node',nodePaths:[dir+'node_modules']})
const compiled=new URL('./.compiled-photo.mjs',import.meta.url)
writeFileSync(compiled,bundled.outputFiles[0].text)
const {parseVisualCard,safeCardUrl,visualCardsRenderer,visualCardRenderer}=await import(compiled.href)
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

test('model card omissions, wrong types and oversize values fail closed',()=>{
 const attrs=attrsOf(product)
 for(const field of ['kind','title','summary','fact1','caveat','source','image','alt']){
  const candidate={...attrs};delete candidate[field]
  assert.throws(()=>parseVisualCard(candidate),field)
 }
 for(const candidate of [null,[],Object.create({title:'inherited'}),{...attrs,title:42},{...attrs,title:' '},
  {...attrs,title:'x'.repeat(91)},{...attrs,summary:'x'.repeat(181)},{...attrs,fact2:'x'.repeat(101)},
  {...attrs,caveat:'x'.repeat(181)},{...attrs,price:'x'.repeat(81),pricenote:'source'},
  {...attrs,price:'value',pricenote:'x'.repeat(121)},
  {...attrs,image:'https://example.com/'+'x'.repeat(590)},
  {...attrs,source:'https://example.com/'+'x'.repeat(580),image:'https://example.com/'+'x'.repeat(580),summary:'x'.repeat(180),caveat:'x'.repeat(180),fact1:'x'.repeat(100),fact2:'x'.repeat(100),fact3:'x'.repeat(100),fact4:'x'.repeat(100)}]){
  assert.equal(visualCardRenderer({attrs:candidate}).props.role,'alert')
 }
})
test('model groups reject bad prefixes, mixed schema and invalid peers atomically',()=>{
 const a=Object.fromEntries(Object.entries(attrsOf(product)).map(([k,v])=>['a_'+k,v]))
 for(const attrs of [Object.assign(Object.create({inherited:'value'}),a),{},{title:'wrong schema'},{...a,f_title:'sixth'},{...a,a_extra:'unknown'},
  {...a,b_title:'incomplete peer'},Object.fromEntries(Object.entries(a).map(([k,v])=>[k.replace('a_','b_'),v])),
  {...a,a_title:17},{...a,z_source:'https://example.com'}]){
  assert.equal(visualCardsRenderer({attrs}).props.role,'alert')
 }
 assert.equal(visualCardsRenderer({attrs:a,streaming:true}).props.role,'status')
 assert.equal(visualCardRenderer({attrs:attrsOf(product),streaming:true}).props.role,'status')
})
