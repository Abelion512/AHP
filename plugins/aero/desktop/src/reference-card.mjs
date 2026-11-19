import React,{useState,useRef,useEffect,useLayoutEffect} from 'react';
import {referenceCss} from './reference-style.mjs';

// Photo controls act only on the supplied image. Card body opens the product/place detail
// dialog; the image button opens only the image viewer. No commerce or map action.
export function VisualCard({data,sessionId,hostState}){
 const [failed,setFailed]=useState(false),[expanded,setExpanded]=useState(false),[zoom,setZoom]=useState(false),[detail,setDetail]=useState(false);
 const viewer=useRef(null),detailDialog=useRef(null),opener=useRef(null),restoreFocus=useRef(true),e=React.createElement;
 const sourceHost=new URL(data.source).hostname;
 const sourceLabel=data.kind==='product'?'Lihat produk':'Buka sumber';
 const closeViewer=()=>viewer.current?.close();
 const closeDetail=()=>detailDialog.current?.close();
 const abandon=()=>{restoreFocus.current=false;const previous=opener.current;opener.current=null;if(viewer.current?.open)viewer.current.close();if(detailDialog.current?.open)detailDialog.current.close();if(document.activeElement===previous)previous?.blur();setExpanded(false);setZoom(false);setDetail(false)};
 // Retained transcript mounts must never leave a top-layer photo or detail over another chat.
 useLayoutEffect(()=>{abandon();return ()=>{restoreFocus.current=false;const previous=opener.current;opener.current=null;if(viewer.current?.open)viewer.current.close();if(detailDialog.current?.open)detailDialog.current.close();if(document.activeElement===previous)previous?.blur()}},[sessionId]);
 useEffect(()=>{
  if(!expanded&&!detail)return;
  const atoms=[hostState.activeSessionId,hostState.focusedSessionId,hostState.focusedStoredSessionId,hostState.connectionId];
  const snapshot=atoms.map(atom=>atom.get());
  const unlisten=atoms.map((atom,i)=>atom.listen(value=>{if(value!==snapshot[i])abandon()}));
  return ()=>unlisten.forEach(off=>off());
 },[expanded,detail,sessionId]);
 const openViewer=event=>{restoreFocus.current=true;opener.current=event.currentTarget;setExpanded(true);setZoom(false);viewer.current?.showModal()};
 const openDetail=event=>{restoreFocus.current=true;if(event.currentTarget?.focus)opener.current=event.currentTarget;setDetail(true);detailDialog.current?.showModal()};
 // Clicks on plain card text open the detail; clicks on the image, links or controls do not.
 const bodyClick=event=>{if(event.target.closest('button,a,select,input,textarea,dialog'))return;openDetail(event)};
 const restore=()=>{setExpanded(false);setZoom(false);setDetail(false);if(restoreFocus.current&&opener.current?.isConnected)opener.current.focus({preventScroll:true})};
 const dialogKeys=closeFn=>event=>{
  if(event.key==='Escape'){event.preventDefault();event.stopPropagation();closeFn()}
  if(event.key==='Tab'){
   const controls=[...event.currentTarget.querySelectorAll('button,select,a[href]')],first=controls[0],last=controls.at(-1);
   if(event.shiftKey&&document.activeElement===first){event.preventDefault();last?.focus()}
   else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first?.focus()}
   event.stopPropagation();
  }
 };
 return e('article',{className:'hermes-visual-card','aria-label':`${data.kind==='product'?'Produk':'Tempat'}: ${data.title}`,onClick:bodyClick},
  e('style',null,referenceCss),
  failed?e('div',{className:'vc-image'},e('p',{className:'vc-failed',role:'status'},'Gambar tidak dapat dimuat. Informasi dan sumber tetap tersedia.')):
   e('button',{className:'vc-image',type:'button','aria-label':'Perbesar gambar '+data.title,onClick:openViewer},e('img',{src:data.image,alt:data.alt,referrerPolicy:'no-referrer',loading:'eager',decoding:'async',onError:()=>setFailed(true)})),
  // Title stays visually plain text; it is the keyboard-reachable detail opener.
  e('h3',null,e('button',{className:'vc-title',type:'button','aria-label':'Detail '+data.title,onClick:openDetail},data.title)),
  data.price?e('div',{className:'vc-price'},data.price):null,
  data.pricenote?e('p',{className:'vc-price-note'},data.pricenote):null,
  e('ul',{className:'vc-facts'},...data.facts.map((x,i)=>e('li',{key:i},x))),
  e('p',{className:'vc-summary'},data.summary),e('p',{className:'vc-caveat'},data.caveat),
  e('a',{className:'vc-source vc-button',href:data.source,target:'_blank',rel:'noopener noreferrer',referrerPolicy:'no-referrer'},sourceLabel),
  e('dialog',{className:'vc-viewer',role:'dialog',ref:viewer,'aria-label':'Gambar '+data.title,
   onClose:restore,
   onCancel:event=>{event.preventDefault();event.stopPropagation();closeViewer()},
   onKeyDown:dialogKeys(closeViewer)},
   e('div',{className:'vc-toolbar'},e('span',null,'Image'),e('div',{className:'vc-controls'},
    e('select',{'aria-label':'Zoom gambar',value:zoom?'100':'fit',onChange:event=>setZoom(event.target.value==='100')},e('option',{value:'fit'},'Fit'),e('option',{value:'100'},'100%')),
    e('button',{className:'vc-close',type:'button','aria-label':'Tutup',title:'Tutup',onClick:closeViewer},'×'))),
   e('div',{className:'vc-stage','data-zoom':String(zoom)},e('img',{className:'vc-large',src:expanded?data.image:undefined,alt:data.alt,referrerPolicy:'no-referrer',onClick:()=>setZoom(v=>!v)})),
   e('div',{className:'vc-attribution'},e('a',{href:data.source,target:'_blank',rel:'noopener noreferrer',referrerPolicy:'no-referrer'},sourceHost+' · '+data.alt))
  ),
  e('dialog',{className:'vc-detail',role:'dialog',ref:detailDialog,'aria-label':'Detail '+data.title,
   onClose:restore,
   onCancel:event=>{event.preventDefault();event.stopPropagation();closeDetail()},
   onKeyDown:dialogKeys(closeDetail)},
   e('div',{className:'vc-toolbar'},e('span',null,data.kind==='product'?'Produk':'Tempat'),e('div',{className:'vc-controls'},
    e('button',{className:'vc-close',type:'button','aria-label':'Tutup',title:'Tutup',onClick:closeDetail},'×'))),
   detail?e('div',{className:'vc-detail-body'},
    e('h3',null,data.title),
    data.price?e('div',{className:'vc-price'},data.price):null,
    data.pricenote?e('p',{className:'vc-price-note'},data.pricenote):null,
    e('ul',{className:'vc-facts'},...data.facts.map((x,i)=>e('li',{key:i},x))),
    e('p',{className:'vc-summary'},data.summary),e('p',{className:'vc-caveat'},data.caveat),
    e('a',{className:'vc-source vc-button',href:data.source,target:'_blank',rel:'noopener noreferrer',referrerPolicy:'no-referrer'},sourceLabel)
   ):null
  )
 );
}
