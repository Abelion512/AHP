/**
 * aero — native Intelligence UI cards rendered inline in the
 * WebApp/Desktop transcript via the plugin transcript-directive area.
 *
 * Install: symlink the `desktop/` folder into
 *   $HERMES_HOME/desktop-plugins/aero
 * Use in a reply (alone on its own line):
 *   ::ui{version="1" id="wiz-01" kind="wizard"  title="Rotasi" steps="OpenCode|Hermes|9router"}
 *   ::ui{version="1" id="stat-01" kind="status"  title="Gate" items="Hook:siap|Credential:blocked"}
 *   ::ui{version="1" id="trace-01" kind="trace"   title="Kenapa" steps="Input|Bukti|Keputusan"}
 *   ::ui{version="1" id="cmp-01" kind="compare" title="Opsi" left="A|B" right="C|D" pick="left"}
 *   ::ui{version="1" id="form-01" kind="form"    title="Input" fields="Nama|Catatan" submit="Kirim"}
 *
 * All attrs are untrusted strings. They are capped, never parsed as markup,
 * and rendered as React text children. No direct network; user clicks submit only through the owning chat composer.
 */
import { jsx as renderJsx, jsxs as renderJsxs } from 'react/jsx-runtime'
import { useEffect, useState, useId } from 'react'
import { TRANSCRIPT_DIRECTIVE_AREA, host, haptic } from '@hermes/plugin-sdk'
import { normalizeInterview, normalizeQuiz, InterviewView, QuizView } from './forms.mjs'

// The SDK consumes plain JS, so pass keys separately just as compiled JSX does.
function jsx(type, props, identity) {
  const { key, ...rest } = props
  return renderJsx(type, rest, identity ?? key)
}
function jsxs(type, props, identity) {
  const { key, ...rest } = props
  return renderJsxs(type, rest, identity ?? key)
}

const ID = 'aero'
const VERSION = '1'
// One allowed catalog is used by validation and rendering. Models describe data,
// never executable expressions, component imports or arbitrary styling.
export const catalog = Object.freeze({
  wizard: { input: 'steps', max: 8 }, status: { input: 'items', max: 8 },
  trace: { input: 'steps', max: 8 }, compare: { input: 'left', max: 6 },
  form: { input: 'fields', max: 6 },
  choice: { input: 'options', max: 6, min: 2, event: 'answer' },
  flow: { input: 'nodes', max: 6, min: 2, event: 'local' },
  chart: { input: 'labels', max: 6, min: 1, event: 'local' },
  interview: { input: 'groups', max: 4, min: 1, event: 'answer' },
  quiz: { input: 'questions', max: 5, min: 1, event: 'local' },
  table: { input: 'columns', max: 5, min: 1, event: 'local' },
  map: { input: 'places', max: 5, min: 1, event: 'local' },
})
const KINDS = new Set(Object.keys(catalog))

// Normalize the new data-rich cards into a small typed representation first.
// Legacy five-kind inputs retain their established caps and behavior.
export function normalize(attrs) {
  const kind = text(attrs.kind, 20)
  if (!['choice', 'flow', 'chart', 'interview', 'quiz', 'table', 'map'].includes(kind)) return null
  if (kind === 'interview') return normalizeInterview(attrs)
  if (kind === 'quiz') return normalizeQuiz(attrs)
  if (kind === 'map') return normalizeMap(attrs)
  const spec = catalog[kind]
  const raw = attrs[spec.input]
  // Keep allocation bounded even if a future caller bypasses the host parser.
  if ((attrs.details?.length || 0) > 2048 || (attrs.values?.length || 0) > 256) return { error: 'Data kartu terlalu panjang.' }
  if (typeof raw !== 'string' || raw.length > 2048) return { error: 'Data kartu belum lengkap. Gunakan jawaban teks.' }
  const values = raw.split('|').map(v => v.trim())
  if (values.length < spec.min || values.length > spec.max || values.some(v => !v || v.length > 60)) {
    return { error: 'Data kartu tidak valid. Gunakan jawaban teks.' }
  }
  if (kind === 'choice') return normalizeChoice(attrs, values)
  if (kind === 'flow') return normalizeFlow(attrs, values)
  if (kind === 'table') return normalizeTable(attrs, values)
  return normalizeChart(attrs, values)
}

function normalizeChoice(attrs, values) {
  if (attrs.multiple !== undefined && !['true', 'false'].includes(attrs.multiple)) return { error: 'Mode pilihan tidak didukung.' }
  if (new Set(values).size !== values.length) return { error: 'Pilihan harus berbeda.' }
  return { kind: 'choice', options: values, multiple: attrs.multiple === 'true' }
}

function normalizeFlow(attrs, values) {
  const details = typeof attrs.details === 'string' ? attrs.details.split('|').map(v => v.trim()) : []
  if (details.length !== values.length || details.some(v => !v || v.length > 180)) return { error: 'Setiap tahap perlu penjelasan singkat.' }
  return { kind: 'flow', nodes: values, details }
}

function normalizeChart(attrs, values) {
  const numbers = typeof attrs.values === 'string' ? attrs.values.split('|').map(v => v.trim()) : []
  if (numbers.length !== values.length || numbers.some(v => !/^(?:0|[1-9]\d{0,8})(?:\.\d{1,4})?$/.test(v))) {
    return { error: 'Angka grafik tidak valid. Nilai harus nonnegatif dan berpasangan dengan label.' }
  }
  return { kind: 'chart', labels: values, values: numbers.map(Number), unit: text(attrs.unit, 16), source: text(attrs.source, 100) }
}

function normalizeTable(attrs, values) {
  if (typeof attrs.rows !== 'string' || attrs.rows.length > 2048) return { error: 'Data tabel belum lengkap. Gunakan jawaban teks.' }
  const rows = attrs.rows.split('|').map(v => v.trim()).filter(v => v !== '')
  if (!rows.length || rows.length > 8) return { error: 'Data tabel tidak valid. Gunakan jawaban teks.' }
  const cells = rows.map(row => row.split(';').map(c => c.trim()))
  if (cells.some(r => r.length !== values.length || r.some(c => !c || c.length > 60))) return { error: 'Setiap baris tabel harus berpasangan dengan kolom.' }
  return { kind: 'table', columns: values, rows: cells }
}

function normalizeMap(attrs) {
  if (typeof attrs.places !== 'string' || attrs.places.length > 2048) return { error: 'Data peta belum lengkap. Gunakan jawaban teks.' }
  const parts = attrs.places.split('|').map(v => v.trim()).filter(v => v !== '')
  if (!parts.length || parts.length > 5) return { error: 'Data peta tidak valid. Gunakan jawaban teks.' }
  const places = parts.map(part => {
    const f = part.split(';').map(x => x.trim())
    return { name: f[0] || '', lat: Number(f[1]), lon: Number(f[2]), note: f[3] || '' }
  })
  const bad = places.some(pl => !pl.name || pl.name.length > 40 || pl.note.length > 60 ||
    !Number.isFinite(pl.lat) || !Number.isFinite(pl.lon) || Math.abs(pl.lat) > 85 || Math.abs(pl.lon) > 180)
  if (bad) return { error: 'Setiap tempat perlu nama;lintang;bujur yang valid.' }
  return { kind: 'map', places }
}

function text(value, max) {
  return typeof value === 'string' ? value.trim().slice(0, max) : ''
}

function items(value, max) {
  if (typeof value !== 'string') return []
  return value.slice(0, 16384)
    .split('|')
    .map((part) => part.trim().slice(0, 60))
    .filter(Boolean)
    .slice(0, max)
}

function send(sessionId, prompt, setError) {
  if (typeof sessionId !== 'string' || !sessionId.trim()) {
    setError('Chat pemilik kartu tidak tersedia. Tidak ada pesan dikirim.')
    return
  }
  if (prompt.length > 240) {
    setError('Pesan melebihi 240 karakter. Pendekkan isian; tidak ada pesan dikirim.')
    return
  }
  try {
    const accepted = host?.composer?.submit?.(sessionId, prompt)
    if (accepted !== true) {
      setError('Composer tidak menerima permintaan ini.')
      return
    }
  } catch {
    setError('Composer tidak menerima permintaan ini.')
    return
  }
  setError('')
  try { haptic('tap') } catch { /* Optional feedback cannot undo an accepted send. */ }
}

function restoreDone(storage, storageKey, rows) {
  try {
    const saved = storageKey ? storage?.get?.(storageKey) : null
    if (!Array.isArray(saved)) return []
    const result = []
    const used = new Set()
    for (const label of saved.slice(0, 8)) {
      if (typeof label !== 'string') continue
      const index = rows.findIndex((row, i) => row === label && !used.has(i))
      if (index >= 0) { used.add(index); result.push(index) }
    }
    return result
  } catch { return [] }
}

function renderChoice(p) {
  const { model, owner, title, button, line, muted, choiceName, selection, setSelection, note, setNote, setError } = p
  const children = []
    children.push(jsxs('fieldset', {
      className: 'aero-choice', key: 'choices', style: { border: 0, margin: '10px 0', padding: 0, minWidth: 0 },
      children: [
        jsx('legend', { style: muted, children: model.multiple ? 'Pilih satu atau lebih' : 'Pilih satu' }),
        ...model.options.map((label, index) => jsxs('label', {
          key: index, style: { ...line, display: 'flex', alignItems: 'center', gap: 10, minHeight: 44, cursor: 'pointer' },
          children: [jsx('input', {
            type: model.multiple ? 'checkbox' : 'radio', name: choiceName, checked: selection.includes(index),
            onChange: () => setSelection(prev => model.multiple ? (prev.includes(index) ? prev.filter(i => i !== index) : [...prev, index]) : [index]),
          }), jsx('span', { children: label })],
        })),
      ],
    }))
    children.push(jsxs('label', { key: 'note', style: { display: 'block', ...muted }, children: [
      jsx('span', { children: 'Catatan opsional' }),
      jsx('input', { type: 'text', maxLength: 80, autoComplete: 'off', value: note,
        onChange: e => setNote(e.target.value.slice(0, 80)),
        style: { display: 'block', width: '100%', boxSizing: 'border-box', minHeight: 40, marginTop: 4, padding: 8, color: 'inherit', background: 'transparent', border: '1px solid var(--ui-stroke-secondary, var(--border))', borderRadius: 6 } }),
    ] }))
    children.push(jsx('button', { key: 'answer', type: 'button', disabled: !owner || selection.length === 0,
      style: { ...button, marginTop: 10, opacity: !owner || selection.length === 0 ? 0.5 : 1 },
      onClick: () => {
        if (!selection.length) return
        const labels = model.options.filter((_, i) => selection.includes(i))
        send(owner, `Jawaban: ${title} - ${labels.join('; ')}${note.trim() ? '; Catatan: ' + note.trim() : ''}`, setError)
      }, children: 'Kirim jawaban' }))

  return children
}

function renderFlow(p) {
  const { model, button, line, muted, stage, setStage } = p
  const children = []

    children.push(jsx('p', { key: 'hint', style: muted, children: 'Pilih tahap untuk melihat hubungan dan penjelasannya.' }))
    children.push(jsx('style', { key: 'flow-layout', children: '@container (max-width:520px){.aero-flow{flex-direction:column}.aero-flow>li{flex:none!important;flex-direction:column}.aero-flow>li>button{width:100%}.aero-flow>li>span{transform:rotate(90deg)}}' }))
    children.push(jsx('ol', { key: 'flow', className: 'aero-flow', 'aria-label': 'Alur', style: { listStyle: 'none', margin: '10px 0', padding: 0, display: 'flex', flexWrap: 'nowrap', gap: 8 },
      children: model.nodes.map((label, index) => jsxs('li', { key: index, style: { display: 'flex', alignItems: 'center', gap: 8, flex: '1 1 0', minWidth: 0 }, children: [
        jsx('button', { type: 'button', 'aria-pressed': stage === index, onClick: () => setStage(index), style: { ...button, flex: 1, minWidth: 0, minHeight: 64, background: stage === index ? 'var(--ui-accent-muted, #2461b412)' : 'transparent', borderColor: stage === index ? 'var(--ui-accent, var(--accent))' : 'var(--ui-stroke-secondary, var(--border))' }, children: `${index + 1}. ${label}` }),
        index < model.nodes.length - 1 ? jsx('span', { 'aria-hidden': true, children: '→' }) : null,
      ] })),
    }))
    children.push(jsxs('div', { key: 'explanation', role: 'status', style: { ...line, padding: '12px 0' }, children: [
      jsx('strong', { children: model.nodes[stage] }),
      jsx('p', { style: { margin: '6px 0', lineHeight: 1.6 }, children: model.details[stage] }),
      jsx('div', { style: muted, children: stage + 1 < model.nodes.length ? `Berikutnya: ${model.nodes[stage + 1]}` : 'Tahap akhir' }),
    ] }))

  return children
}

function renderChart(p) {
  const { model, title, button, line, muted, stage, setStage, table, setTable } = p
  const children = []

    const max = Math.max(...model.values) || 1
    children.push(jsx('p', { key: 'chart-hint', style: muted, children: 'Bandingkan panjang batang; angka tetap ditampilkan. Pilih batang untuk fokus.' }))
    children.push(jsx('div', { key: 'bars', role: 'group', 'aria-label': 'Grafik batang', children: model.labels.map((label, index) => jsxs('button', {
      key: index, type: 'button', 'aria-pressed': stage === index, onClick: () => setStage(index),
      style: { ...button, display: 'block', textAlign: 'left', width: '100%', padding: '10px 8px', margin: '6px 0', color: 'var(--foreground)', borderColor: stage === index ? 'var(--ui-accent, var(--accent))' : 'var(--ui-stroke-secondary, var(--border))' },
      children: [
        jsxs('span', { style: { display: 'flex', justifyContent: 'space-between', gap: 8 }, children: [jsx('span', { children: label }), jsx('strong', { children: `${model.values[index]}${model.unit ? ' ' + model.unit : ''}` })] }),
        jsx('span', { 'aria-hidden': true, style: { display: 'block', height: 10, background: 'var(--ui-stroke-secondary, var(--border))', marginTop: 8, borderRadius: 3 }, children: jsx('span', { style: { display: 'block', height: '100%', width: `${100 * model.values[index] / max}%`, background: 'var(--ui-accent, var(--accent))', borderRadius: 3 } }) }),
      ],
    })) }))
    children.push(jsx('div', { key: 'focus', role: 'status', style: muted, children: `Fokus: ${model.labels[stage]} = ${model.values[stage]}${model.unit ? ' ' + model.unit : ''}` }))
    if (model.source) children.push(jsx('p', { key: 'source', style: muted, children: `Sumber: ${model.source}` }))
    children.push(jsx('button', { key: 'table-toggle', type: 'button', 'aria-expanded': table, onClick: () => setTable(v => !v), style: { ...button, marginTop: 8 }, children: table ? 'Tutup tabel data' : 'Tabel data' }))
    if (table) children.push(jsxs('table', { key: 'table', style: { width: '100%', borderCollapse: 'collapse', marginTop: 8 }, children: [
      jsx('caption', { style: muted, children: title }),
      jsx('thead', { children: jsxs('tr', { children: [jsx('th', { scope: 'col', style: { ...line, textAlign: 'left' }, children: 'Label' }), jsx('th', { scope: 'col', style: line, children: model.unit || 'Nilai' })] }) }),
      jsx('tbody', { children: model.labels.map((label, index) => jsxs('tr', { key: index, children: [jsx('th', { scope: 'row', style: { ...line, textAlign: 'left' }, children: label }), jsx('td', { style: { ...line, textAlign: 'center' }, children: model.values[index] })] })) }),
    ] }))
  return children
}

function renderTable(p) {
  const { model, line } = p
  const head = { padding: '9px 8px 9px 0', borderBottom: '1px solid var(--ui-stroke-secondary, var(--border))', textAlign: 'left', fontWeight: 600 }
  return [jsx('div', { key: 'table-wrap', style: { overflowX: 'auto', marginTop: 8 }, children: jsxs('table', { style: { width: '100%', borderCollapse: 'collapse' }, children: [
    jsx('thead', { children: jsxs('tr', { children: model.columns.map((col, i) => jsx('th', { key: i, scope: 'col', style: head, children: col })) }) }),
    jsx('tbody', { children: model.rows.map((row, ri) => jsxs('tr', { key: ri, children: row.map((cell, ci) => jsx('td', { key: ci, style: { ...line, textAlign: 'left', paddingRight: 8 }, children: cell })) })) }),
  ] }) })]
}

function renderMap(p) {
  const { model, muted } = p
  const n = model.places.length
  const latC = model.places.reduce((sum, x) => sum + x.lat, 0) / n
  const lonC = model.places.reduce((sum, x) => sum + x.lon, 0) / n
  const latSpan = Math.max(...model.places.map(x => x.lat)) - Math.min(...model.places.map(x => x.lat))
  const lonSpan = Math.max(...model.places.map(x => x.lon)) - Math.min(...model.places.map(x => x.lon))
  const span = Math.max(latSpan, lonSpan)
  const zoom = span > 5 ? 9 : span > 2 ? 10 : span > 1 ? 11 : span > 0.4 ? 12 : span > 0.15 ? 13 : 14
  const scale = 2 ** zoom
  const toX = lon => (lon + 180) / 360 * scale
  const toY = lat => { const r = lat * Math.PI / 180; return (1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2 * scale }
  const cx = Math.floor(toX(lonC))
  const cy = Math.floor(toY(latC))
  const tiles = []
  for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
    const tx = ((cx + dx) % scale + scale) % scale
    const ty = Math.min(Math.max(cy + dy, 0), scale - 1)
    tiles.push({ key: `${zoom}/${tx}/${ty}`, src: `https://tile.openstreetmap.org/${zoom}/${tx}/${ty}.png` })
  }
  const pins = model.places.map((pl, i) => ({
    ...pl, i,
    left: Math.min(Math.max((toX(pl.lon) - (cx - 1)) / 3 * 100, 2), 98),
    top: Math.min(Math.max((toY(pl.lat) - (cy - 1)) / 3 * 100, 6), 94),
  }))
  return [jsxs('div', { key: 'map', style: { marginTop: 8 }, children: [
    jsxs('div', { key: 'grid', style: { position: 'relative', display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', overflow: 'hidden', borderRadius: 8, border: '1px solid var(--ui-stroke-secondary, var(--border))' }, children: [
      ...tiles.map(t => jsx('img', { key: t.key, src: t.src, alt: '', loading: 'lazy', draggable: false, style: { width: '100%', display: 'block', userSelect: 'none' } })),
      ...pins.map(pl => jsxs('div', { key: 'pin' + pl.i, style: { position: 'absolute', left: pl.left + '%', top: pl.top + '%', transform: 'translate(-50%, -100%)', textAlign: 'center', pointerEvents: 'none' }, children: [
        jsx('div', { key: 'dot', style: { width: 10, height: 10, margin: '0 auto', borderRadius: '50%', background: '#000', border: '2px solid #fff' } }),
        jsxs('div', { key: 'lbl', style: { ...muted, marginTop: 2, padding: '1px 4px', background: 'rgba(255,255,255,0.85)', borderRadius: 4, display: 'inline-block', color: '#000' }, children: pl.name }),
      ] })),
    ] }),
    jsxs('div', { key: 'attr', style: { ...muted, marginTop: 4 }, children: ['Peta statis - bukan peta interaktif. © ', jsx('a', { key: 'osm', href: 'https://www.openstreetmap.org/copyright', target: '_blank', rel: 'noreferrer', children: 'OpenStreetMap contributors' })] }),
  ] })]
}

function Card({ attrs, streaming, sessionId, storage }) {
  const rawKind = typeof attrs.kind === 'string' ? attrs.kind.trim() : ''
  const version = typeof attrs.version === 'string' ? attrs.version.trim() : VERSION
  const cardId = text(attrs.id, 60)
  const owner = typeof sessionId === 'string' && sessionId.trim() ? sessionId : null
  const storageKey = owner && cardId ? JSON.stringify([ID, VERSION, owner, cardId]) : null
  const rows = items(attrs.steps || attrs.items, 8)
  const [done, setDone] = useState(() => restoreDone(storage, storageKey, rows))
  const [error, setError] = useState('')
  const [values, setValues] = useState({})
  const choiceName = useId()
  const [selection, setSelection] = useState([])
  const [note, setNote] = useState('')
  const [stage, setStage] = useState(0)
  const [table, setTable] = useState(false)
  const model = normalize(attrs)

  useEffect(() => {
    try {
      if (storageKey && !streaming && (!rawKind || rawKind === 'wizard') && version === VERSION) {
        storage?.set?.(storageKey, done.map((i) => rows[i]).filter((row) => typeof row === 'string'))
      }
    } catch { /* Persistence is best-effort; local state remains usable. */ }
  }, [storage, storageKey, done, streaming, rawKind, version, rows.join('\u0000')])

  if (version !== VERSION || (rawKind && !KINDS.has(rawKind))) {
    return jsx('div', { role: 'status', children: 'Kartu UI tidak didukung; gunakan jawaban teks.' })
  }
  if (streaming) {
    return jsx('div', { role: 'status', children: 'Menyiapkan kartu...' })
  }
  if (model?.error) return jsx('div', { role: 'status', children: model.error })
  const kind = rawKind || 'wizard'
  const title = text(attrs.title, 80) || 'Aero'

  const shell = {
    maxWidth: 760,
    containerType: 'inline-size',
    padding: '12px 2px 10px',
    color: 'var(--foreground)',
    fontSize: 13,
    overflowWrap: 'anywhere',
  }
  const muted = { color: 'var(--ui-text-secondary, var(--muted-foreground))', fontSize: 12 }
  const line = { borderTop: '1px solid var(--ui-stroke-secondary, var(--border))', padding: '9px 0' }
  const dot = { width: 8, height: 8, borderRadius: 99, flex: '0 0 8px', marginTop: 4 }
  const button = {
    font: 'inherit',
    fontSize: 12,
    minHeight: 40,
    padding: '8px 12px',
    borderRadius: 6,
    border: '1px solid var(--ui-stroke-secondary, var(--border))',
    background: 'transparent',
    color: 'var(--ui-accent, var(--accent))',
    cursor: 'pointer',
  }

  const children = []

  children.push(
    jsxs('div', {
      key: 'head',
      style: { display: 'flex', gap: 10, alignItems: 'baseline', flexWrap: 'wrap' },
      children: [
        jsx('div', { style: { fontSize: 17, fontWeight: 650 }, children: title }),
        rows.length && kind === 'wizard'
          ? jsx('div', { style: muted, children: `${done.length} / ${rows.length}` })
          : null,
      ],
    })
  )

  if (kind === 'wizard') {
    const pct = rows.length ? Math.round((done.length / rows.length) * 100) : 0
    children.push(
      jsx('div', {
        key: 'bar',
        style: {
          height: 3,
          margin: '10px 0',
          borderRadius: 99,
          overflow: 'hidden',
          background: 'var(--ui-stroke-secondary, var(--border))',
        },
        children: jsx('div', {
          style: { width: `${pct}%`, height: '100%', background: 'var(--ui-accent, var(--accent))' },
        }),
      })
    )
    rows.forEach((row, index) => {
      const isDone = done.includes(index)
      children.push(
        jsxs('div', {
          key: `w${index}`,
          style: { ...line, display: 'flex', gap: 11, alignItems: 'flex-start', opacity: isDone ? 0.55 : 1 },
          children: [
            jsx('div', {
              style: {
                flex: '0 0 24px',
                height: 24,
                borderRadius: 99,
                border: '1px solid var(--ui-stroke-secondary, var(--border))',
                display: 'grid',
                placeItems: 'center',
                fontSize: 12,
              },
              children: isDone ? '✓' : String(index + 1),
            }),
            jsxs('div', {
              style: { flex: 1, minWidth: 0 },
              children: [
                jsx('div', { children: row }),
                jsxs('div', { style: { display: 'flex', gap: 6, marginTop: 7 }, children: [
                  jsx('button', {
                    type: 'button',
                    style: button,
                    onClick: () => send(owner, `Bantu: ${title} - ${row}`, setError),
                    children: 'Bantu',
                  }),
                  jsx('button', {
                    type: 'button',
                    style: { ...button, color: 'var(--ui-text-secondary, var(--muted-foreground))' },
                    onClick: () =>
                      setDone((prev) => (prev.includes(index) ? prev.filter((n) => n !== index) : [...prev, index])),
                    children: isDone ? 'Batal' : 'Sudah',
                  }),
                ] }),
              ],
            }),
          ],
        })
      )
    })
  } else if (kind === 'status') {
    rows.forEach((row, index) => {
      const parts = row.split(':')
      const label = text(parts[0], 60)
      const state = text(parts.slice(1).join(':'), 24).toLowerCase()
      const good = ['pass', 'ok', 'allow', 'siap', 'green'].includes(state)
      children.push(
        jsxs('div', {
          key: `s${index}`,
          style: { ...line, display: 'flex', gap: 10, alignItems: 'center' },
          children: [
            jsx('div', {
              style: { ...dot, background: good ? 'var(--ui-accent, var(--accent))' : 'var(--ui-text-quaternary, var(--muted-foreground))' },
            }),
            jsx('div', { style: { flex: 1 }, children: label }),
            jsx('div', { style: muted, children: state || '-' }),
          ],
        })
      )
    })
  } else if (kind === 'compare') {
    const left = items(attrs.left, 6)
    const right = items(attrs.right, 6)
    const pick = text(attrs.pick, 6) === 'right' ? 1 : 0
    children.push(
      jsxs('div', {
        key: 'cmp',
        style: { display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr)', gap: 12, marginTop: 10 },
        children: [left, right].map((col, ci) =>
          jsxs('div', {
            key: `c${ci}`,
            style: {
              border: '1px solid var(--ui-stroke-secondary, var(--border))',
              borderRadius: 8,
              padding: 10,
              outline: ci === pick ? '1px solid var(--ui-accent, var(--accent))' : 'none',
            },
            children: [
              jsx('div', { style: { ...muted, marginBottom: 6 }, children: ci === 0 ? 'A' : 'B' }),
              ...col.map((value, index) =>
                jsx('div', {
                  key: `v${index}`,
                  style: { padding: '5px 0', borderTop: '1px solid var(--ui-stroke-secondary, var(--border))' },
                  children: value,
                })
              ),
            ],
          })
        ),
      })
    )
  } else if (kind === 'form') {
    const fields = items(attrs.fields, 6)
    const submit = text(attrs.submit, 40) || 'Kirim'
    fields.forEach((field, index) =>
      children.push(
        jsxs('label', {
        key: `f${index}`,
        style: { display: 'block', marginTop: 9, ...muted },
        children: [
          jsx('div', { children: field }),
          jsx('input', {
            type: 'text',
            maxLength: 160,
            autoComplete: 'off',
            value: values[index] || '',
            onChange: (event) =>
              setValues((prev) => ({ ...prev, [index]: event.target.value.slice(0, 160) })),
            style: {
              width: '100%',
              marginTop: 4,
              padding: '8px 10px',
              borderRadius: 6,
              border: '1px solid var(--ui-stroke-secondary, var(--border))',
              background: 'transparent',
              color: 'var(--foreground)',
              font: 'inherit',
              minHeight: 40,
              boxSizing: 'border-box',
            },
          }),
        ],
      })
      )
    )
    children.push(
      jsx('button', {
        key: 'submit',
        type: 'button',
        style: { ...button, marginTop: 10 },
        onClick: () =>
          send(
            owner,
            `${title}: ${fields.map((field, index) => `${field}=${values[index] || ''}`).join('; ')}`,
            setError
          ),
        children: submit,
      })
    )
  } else if (kind === 'trace') {
    const traceChildren = [
      jsx('summary', { key: 'sum', children: `Kenapa - ${rows.length} node` }),
      jsxs('div', {
        key: 'nodes',
        style: { borderLeft: '1px solid var(--ui-stroke-secondary, var(--border))', paddingLeft: 14, marginTop: 8 },
        children: rows.map((row, index) =>
          jsx('div', { key: `t${index}`, style: { marginBottom: 7 }, children: `${index + 1}. ${row}` })
        ),
      }),
    ]
    children.push(
      jsx('details', { key: 'trace', style: { marginTop: 10, ...muted }, children: traceChildren })
    )
  }

  const learningProps = { model, owner, title, button, line, muted, choiceName, selection, setSelection, note, setNote, setError, stage, setStage, table, setTable }
  if (kind === 'choice') children.push(...renderChoice(learningProps))
  else if (kind === 'flow') children.push(...renderFlow(learningProps))
  else if (kind === 'chart') children.push(...renderChart(learningProps))
  else if (kind === 'table') children.push(...renderTable(learningProps))
  else if (kind === 'map') children.push(...renderMap(learningProps))
  else if (kind === 'interview') children.push(jsx(InterviewView, { key: 'interview', model, title, owner, send, setError }))
  else if (kind === 'quiz') children.push(jsx(QuizView, { key: 'quiz', model, title }))

  if (!owner && (kind === 'wizard' || kind === 'form' || kind === 'choice' || kind === 'interview')) children.push(jsx('div', { key: 'owner', role: 'status', children: 'Chat pemilik kartu tidak tersedia. Pengiriman dinonaktifkan.' }))
  if (error) children.push(jsx('div', { key: 'err', role: 'alert', style: { ...muted, marginTop: 8 }, children: error }))

  return jsx('div', { style: shell, children })
}

export default {
  id: ID,
  name: 'Aero',
  register(ctx) {
    ctx.register({
      id: 'ui.directive',
      area: TRANSCRIPT_DIRECTIVE_AREA,
      data: {
        name: 'ui',
        render: ({ attrs, streaming, sessionId }) => {
          const safeAttrs = attrs && typeof attrs === 'object' ? attrs : {}
          // Remount when the owning chat or card content changes. Never write
          // the previous card's progress/form state under a new identity.
          const identity = JSON.stringify([sessionId, safeAttrs])
          return jsx(Card, { attrs: safeAttrs, streaming, sessionId, storage: ctx.storage || null }, identity)
        },
      },
    })
  },
}
