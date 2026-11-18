import {TRANSCRIPT_DIRECTIVE_AREA,host} from '@hermes/plugin-sdk'
import aero from './aero-baseline.js'
import {visualCardRenderer,visualCardsRenderer} from './visual-card.mjs'
// Extend Aero; keep its original ui directive and eight kinds unchanged.
export default {id:aero.id,name:aero.name,register(ctx){
 aero.register(ctx)
 ctx.register({id:'aero.visual-card',area:TRANSCRIPT_DIRECTIVE_AREA,data:{name:'visualcard',render:props=>visualCardRenderer({...props,hostState:host.state})}})
 ctx.register({id:'aero.visual-cards',area:TRANSCRIPT_DIRECTIVE_AREA,data:{name:'visualcards',render:props=>visualCardsRenderer({...props,hostState:host.state})}})
}}
export {catalog,normalize} from './aero-baseline.js'
