// Bounded, informational product/place cards. Not a commerce or map API.
// Source image previews load immediately; no model callback or commerce action. Maps keep native provider consent.
import React,{useState,useRef} from 'react'
const plain=x=>x!==null&&typeof x==='object'&&!Array.isArray(x)&&Object.getPrototypeOf(x)===Object.prototype
const text=(x,n)=>typeof x==='string'&&x.trim()&&x.length<=n?x.trim():null
export function safeCardUrl(raw){
 if(typeof raw!=='string'||raw.length>600)return null
 try{const u=new URL(raw);const h=u.hostname.toLowerCase();if(u.protocol!=='https:'||u.username||u.password||!h.includes('.')||/^(localhost|127\.|0\.|10\.|192\.168\.|169\.254\.|172\.(1[6-9]|2\d|3[01])\.)/.test(h)||h.endsWith('.local')||h.includes(':'))return null;return u.href}catch{return null}
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
  const keys=Object.keys(groups).sort((a,b)=>a.localeCompare(b));if(keys.length<1||keys.length>5||keys[0]!=='a')throw Error('group count')
  return React.createElement('section',{className:'hermes-visual-grid',role:'region',tabIndex:0,'aria-label':'Pilihan kartu visual, geser ke samping'},...keys.map(key=>React.createElement(VisualCard,{key:JSON.stringify(groups[key]),sessionId,hostState,data:parseVisualCard(groups[key])})))
 }catch{return React.createElement('p',{role:'alert'},'Kumpulan kartu tidak valid. Tidak ada tautan atau gambar dibuka.')}
}
