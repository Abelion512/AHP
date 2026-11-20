// Bounded, informational product/place cards. Not a commerce or map API.
// Source image previews load immediately; no model callback or commerce action. Maps keep native provider consent.
import React,{useState,useRef} from 'react'
const plain=x=>x!==null&&typeof x==='object'&&!Array.isArray(x)&&Object.getPrototypeOf(x)===Object.prototype
const text=(x,n)=>typeof x==='string'&&x.trim()&&x.length<=n?x.trim():null
export function safeCardUrl(raw){
 if(typeof raw!=='string'||raw.length>600)return null
 try{
  const u=new URL(raw)
  let h=u.hostname.toLowerCase()
  while(h.endsWith('.'))h=h.slice(0,-1)
  if(u.protocol!=='https:'||u.username||u.password||!h||h.includes(':'))return null
  if(/^[0-9.]+$/.test(h)){
   const parts=h.split('.')
   if(parts.length!==4)return null
   const octets=[]
   for(const part of parts){
    if(!/^(0|[1-9][0-9]{0,2})$/.test(part))return null
    const n=Number(part)
    if(!Number.isInteger(n)||n<0||n>255)return null
    octets.push(n)
   }
   const [a,b,c,d]=octets
   if(a===0||a===10||a===127)return null
   if(a===169&&b===254)return null
   if(a===192&&b===168)return null
   if(a===172&&b>=16&&b<=31)return null
  }else{
   if(!h.includes('.')||h==='localhost'||h.endsWith('.local'))return null
   if(h.split('.').some(label=>!label||label.length>63))return null
  }
  return u.href
 }catch{return null}
}
export function parseVisualCard(attrs){
 if(!plain(attrs)||Object.keys(attrs).some(k=>!['kind','title','summary','fact1','fact2','fact3','fact4','caveat','source','image','alt','price','pricenote'].includes(k))||Object.values(attrs).some(v=>typeof v!=='string'))throw Error('schema')
 if(Object.entries(attrs).reduce((n,[k,v])=>n+k.length+v.length+4,-1)>2000)throw Error('attribute cap')
 if((attrs.price!==undefined||attrs.pricenote!==undefined)&&(!text(attrs.price,80)||!text(attrs.pricenote,120)))throw Error('price requires value and source note')
 const facts=[attrs.fact1,attrs.fact2,attrs.fact3,attrs.fact4].filter(x=>x!==undefined)
 const d={...attrs,facts}
 if(!['product','place'].includes(d.kind)||!text(d.title,90)||!text(d.summary,180)||!safeCardUrl(d.source)||!safeCardUrl(d.image)||!text(d.alt,120)||!text(d.caveat,180)||!text(attrs.fact1,100)||facts.length<1||facts.some(x=>!text(x,100)))throw Error('schema')
 return {...d,title:d.title.trim(),summary:d.summary.trim(),source:safeCardUrl(d.source),image:safeCardUrl(d.image),facts:facts.map(x=>x.trim())}
}
import {VisualCard} from './reference-card.mjs'
export function visualCardRenderer({attrs,streaming,sessionId,hostState}){
 if(streaming)return React.createElement('p',{role:'status'},'Menyiapkan kartu visual...')
 try{const data=parseVisualCard(attrs);return React.createElement(VisualCard,{key:JSON.stringify(attrs),data,streaming,sessionId,hostState})}catch{return React.createElement('p',{role:'alert'},'Kartu produk/tempat tidak valid. Minta data bersumber yang lengkap. Tidak ada tautan atau gambar dibuka.')}
}

export function visualCardsRenderer({attrs,streaming,sessionId,hostState}){
 if(streaming)return React.createElement('p',{role:'status'},'Menyiapkan kartu visual...')
 try{
  if(!plain(attrs)||Object.entries(attrs).reduce((n,[k,v])=>n+k.length+String(v).length+4,-1)>2000)throw Error('group cap')
  const groups={}
  for(const [key,value] of Object.entries(attrs)){const m=/^([abcde])_(.+)$/.exec(key);if(!m)throw Error('group schema');(groups[m[1]]??={})[m[2]]=value}
  const keys=Object.keys(groups).sort((a,b)=>a.localeCompare(b));if(keys.length<1||keys.length>5||keys.some((key,index)=>key!==String.fromCharCode(97+index)))throw Error('group count')
  return React.createElement('section',{className:'hermes-visual-grid',role:'region',tabIndex:0,'aria-label':'Pilihan kartu visual, geser ke samping'},...keys.map(key=>React.createElement(VisualCard,{key:JSON.stringify(groups[key]),sessionId,hostState,data:parseVisualCard(groups[key])})))
 }catch{return React.createElement('p',{role:'alert'},'Kumpulan kartu tidak valid. Tidak ada tautan atau gambar dibuka.')}
}
