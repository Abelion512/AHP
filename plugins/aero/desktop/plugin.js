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
import { jsx, jsxs } from 'react/jsx-runtime'
import { useEffect, useState } from 'react'
import { TRANSCRIPT_DIRECTIVE_AREA, host, haptic } from '@hermes/plugin-sdk'

const ID = 'aero'
const VERSION = '1'
const KINDS = new Set(['wizard', 'status', 'trace', 'compare', 'form'])

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
  const kind = rawKind || 'wizard'
  const title = text(attrs.title, 80) || 'Aero'

  const shell = {
    maxWidth: 760,
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

  if (!owner && (kind === 'wizard' || kind === 'form')) children.push(jsx('div', { key: 'owner', role: 'status', children: 'Chat pemilik kartu tidak tersedia. Pengiriman dinonaktifkan.' }))
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
