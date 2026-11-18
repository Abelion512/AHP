import React,{useState,useRef,useEffect,useLayoutEffect} from 'react';
import {referenceCss} from './reference-style.mjs';

// Photo controls act only on the supplied image. No product-detail or map action.
export function VisualCard({data,sessionId,hostState}){
 const [failed,setFailed]=useState(false),[expanded,setExpanded]=useState(false),[zoom,setZoom]=useState(false);
 const dialog=useRef(null),opener=useRef(null),restoreFocus=useRef(true),e=React.createElement;
 const sourceHost=new URL(data.source).hostname;
 const close=()=>dialog.current?.close();
 const abandon=()=>{restoreFocus.current=false;const previous=opener.current;opener.current=null;if(dialog.current?.open)dialog.current.close();if(document.activeElement===previous)previous?.blur();setExpanded(false);setZoom(false)};
 // Retained transcript mounts must never leave a top-layer photo over another chat.
 useLayoutEffect(()=>{abandon();return ()=>{restoreFocus.current=false;const previous=opener.current;opener.current=null;if(dialog.current?.open)dialog.current.close();if(document.activeElement===previous)previous?.blur()}},[sessionId]);
 useEffect(()=>{
  if(!expanded)return;
  const atoms=[hostState.activeSessionId,hostState.focusedSessionId,hostState.focusedStoredSessionId,hostState.connectionId];
  const snapshot=atoms.map(atom=>atom.get());
  const unlisten=atoms.map((atom,i)=>atom.listen(value=>{if(value!==snapshot[i])abandon()}));
  return ()=>unlisten.forEach(off=>off());
 },[expanded,sessionId]);
 const open=event=>{restoreFocus.current=true;opener.current=event.currentTarget;setExpanded(true);setZoom(false);dialog.current?.showModal()};
 return e('article',{className:'hermes-visual-card','aria-label':`${data.kind==='product'?'Produk':'Tempat'}: ${data.title}`},
  e('style',null,referenceCss),
  failed?e('div',{className:'vc-image'},e('p',{className:'vc-failed',role:'status'},'Gambar tidak dapat dimuat. Informasi dan sumber tetap tersedia.')):
   e('button',{className:'vc-image',type:'button','aria-label':'Perbesar gambar '+data.title,onClick:open},e('img',{src:data.image,alt:data.alt,referrerPolicy:'no-referrer',loading:'eager',decoding:'async',onError:()=>setFailed(true)})),
  // The observed reference title is plain text, separate from the photo action.
  e('h3',null,data.title),
  data.price?e('div',{className:'vc-price'},data.price):null,
  data.pricenote?e('p',{className:'vc-price-note'},data.pricenote):null,
  e('ul',{className:'vc-facts'},...data.facts.map((x,i)=>e('li',{key:i},x))),
  e('p',{className:'vc-summary'},data.summary),e('p',{className:'vc-caveat'},data.caveat),
  e('a',{className:'vc-source',href:data.source,target:'_blank',rel:'noopener noreferrer',referrerPolicy:'no-referrer'},'Sumber'),
  e('dialog',{className:'vc-viewer',role:'dialog',ref:dialog,'aria-label':'Gambar '+data.title,
   onClose:()=>{setExpanded(false);setZoom(false);if(restoreFocus.current&&opener.current?.isConnected)opener.current.focus({preventScroll:true})},
   onCancel:event=>{event.preventDefault();event.stopPropagation();close()},
   onKeyDown:event=>{
    if(event.key==='Escape'){event.preventDefault();event.stopPropagation();close()}
    if(event.key==='Tab'){
     const controls=[...event.currentTarget.querySelectorAll('button,select,a[href]')],first=controls[0],last=controls.at(-1);
     if(event.shiftKey&&document.activeElement===first){event.preventDefault();last?.focus()}
     else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first?.focus()}
     event.stopPropagation();
    }
   }},
   e('div',{className:'vc-toolbar'},e('span',null,'Image'),e('div',{className:'vc-controls'},
    e('select',{'aria-label':'Zoom gambar',value:zoom?'100':'fit',onChange:event=>setZoom(event.target.value==='100')},e('option',{value:'fit'},'Fit'),e('option',{value:'100'},'100%')),
    e('button',{className:'vc-close',type:'button','aria-label':'Tutup',title:'Tutup',onClick:close},'×'))),
   e('div',{className:'vc-stage','data-zoom':String(zoom)},e('img',{className:'vc-large',src:expanded?data.image:undefined,alt:data.alt,referrerPolicy:'no-referrer',onClick:()=>setZoom(v=>!v)})),
   e('div',{className:'vc-attribution'},e('a',{href:data.source,target:'_blank',rel:'noopener noreferrer',referrerPolicy:'no-referrer'},sourceHost+' · '+data.alt))
  )
 );
}
