export const referenceCss = `
.hermes-visual-grid{display:flex;gap:8px;max-width:100%;min-width:0;overflow-x:auto;overscroll-behavior-x:contain;scroll-snap-type:x proximity;align-items:flex-start;margin:16px 18px 16px 0;padding-bottom:8px;scrollbar-width:thin}
.hermes-visual-card{font:inherit;color:inherit;min-width:0;width:100%;max-width:480px;background:transparent}
.hermes-visual-grid .hermes-visual-card{flex:0 0 min(300px,78%);scroll-snap-align:start}
.hermes-visual-card *{box-sizing:border-box}
.hermes-visual-card .vc-image{all:unset;box-sizing:border-box;display:grid;place-items:center;cursor:zoom-in;width:100%;aspect-ratio:1.25;overflow:hidden;border:1px solid color-mix(in srgb,currentColor 12%,transparent);border-radius:16px;background:color-mix(in srgb,currentColor 4%,transparent)}
.hermes-visual-card .vc-image img{display:block;object-fit:contain;width:100%;height:100%;min-height:0}
.hermes-visual-card h3{font-size:16px;line-height:1.4;font-weight:500;overflow-wrap:anywhere;margin:7px 0}
.hermes-visual-card .vc-price{font-size:20px;line-height:1.4;margin:5px 0}.hermes-visual-card .vc-price-note{font-size:12px;line-height:1.5;margin:4px 0 12px;opacity:.7}
.hermes-visual-card .vc-facts{list-style:none;margin:0;padding:0;display:grid;gap:4px;font-size:13px;line-height:1.5}
.hermes-visual-card .vc-summary,.hermes-visual-card .vc-caveat{font-size:12px;line-height:1.5;overflow-wrap:anywhere;margin:8px 0}
.hermes-visual-card .vc-caveat{opacity:.7}
.hermes-visual-card .vc-source{font-size:13px;color:inherit;overflow-wrap:anywhere}
.hermes-visual-card .vc-button{display:inline-flex;align-items:center;min-height:40px;padding:8px 16px;border:1px solid color-mix(in srgb,currentColor 25%,transparent);border-radius:9999px;text-decoration:none;font-weight:500;cursor:pointer;margin:4px 0}
.hermes-visual-card .vc-title{all:unset;display:inline;cursor:pointer;overflow-wrap:anywhere}
.hermes-visual-card dialog.vc-detail{position:fixed;inset:0;box-sizing:border-box;margin:auto;border:1px solid color-mix(in srgb,currentColor 12%,transparent);border-radius:20px;padding:0;width:min(420px,92vw);max-height:80dvh;color:CanvasText;background:Canvas;overflow:hidden}
.hermes-visual-card .vc-detail-body{padding:52px 20px 20px;overflow:auto;max-height:80dvh}
.hermes-visual-card .vc-detail-body h3{font-size:18px;line-height:1.4;font-weight:600;margin:0 0 8px}
.hermes-visual-card .vc-failed{font-size:12px;line-height:1.5;padding:12px;text-align:center}
.hermes-visual-card button:focus-visible,.hermes-visual-card a:focus-visible,.hermes-visual-card select:focus-visible{outline:3px solid #087bff;outline-offset:3px}
.hermes-visual-card dialog.vc-viewer{position:fixed;inset:0;box-sizing:border-box;margin:auto;border:0;border-radius:0;padding:0;width:100vw;max-width:100vw;height:100dvh;max-height:100dvh;color:CanvasText;background:color-mix(in srgb,Canvas 90%,transparent);overflow:hidden}
.hermes-visual-card dialog::backdrop{background:color-mix(in srgb,Canvas 65%,transparent);backdrop-filter:blur(12px)}
.hermes-visual-card .vc-toolbar{position:absolute;z-index:2;top:8px;left:8px;right:8px;display:flex;align-items:center;justify-content:space-between;gap:8px;pointer-events:none}
.hermes-visual-card .vc-toolbar>*{pointer-events:auto;font:inherit;font-size:13px;border:1px solid color-mix(in srgb,currentColor 12%,transparent);color:CanvasText;background:Canvas;box-shadow:0 2px 10px #0001;border-radius:24px;min-height:40px;padding:8px 14px}
.hermes-visual-card .vc-controls{display:flex;gap:8px;margin-left:auto;background:none;border:0;box-shadow:none;padding:0}
.hermes-visual-card .vc-controls select,.hermes-visual-card .vc-close{color:CanvasText;background:Canvas;font:inherit;border:1px solid color-mix(in srgb,currentColor 12%,transparent);border-radius:24px;min-height:40px;padding:8px 12px;cursor:pointer}
.hermes-visual-card .vc-close{width:40px;font-size:24px;line-height:1;padding:0}
.hermes-visual-card .vc-stage{position:absolute;inset:56px 16px 52px;display:flex;align-items:center;justify-content:center;overflow:auto}
.hermes-visual-card .vc-large{display:block;width:auto;height:auto;max-width:100%;max-height:100%;object-fit:contain;cursor:zoom-in}
.hermes-visual-card .vc-stage[data-zoom=true]{display:block;text-align:center}
.hermes-visual-card .vc-stage[data-zoom=true] .vc-large{display:inline-block;max-width:none;max-height:none;cursor:zoom-out}
.hermes-visual-card .vc-attribution{position:absolute;bottom:12px;left:16px;right:16px;text-align:center;font-size:13px;line-height:1.5;overflow-wrap:anywhere}
.hermes-visual-card .vc-attribution a{color:CanvasText}
@media(max-width:600px){.hermes-visual-card .vc-stage{inset:58px 8px 78px}.hermes-visual-card .vc-attribution{font-size:12px}.hermes-visual-card .vc-summary,.hermes-visual-card .vc-caveat{font-size:12px}}
.hermes-visual-card .vc-image{border-radius:18px}
.aero-choice label{border:1px solid color-mix(in srgb,currentColor 10%,transparent)!important;border-radius:14px;padding:12px 14px!important;margin:8px 0;background:color-mix(in srgb,currentColor 5%,transparent)}.aero-choice label:has(input:checked){border-color:currentColor!important;background:color-mix(in srgb,currentColor 9%,transparent)}.aero-choice label:has(input:checked)::after{content:"\\2713";margin-left:auto}
`;
