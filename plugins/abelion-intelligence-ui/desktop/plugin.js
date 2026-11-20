/**
 * abelion-intelligence-ui — native Intelligence UI cards rendered inline in the
 * WebApp/Desktop transcript via the plugin transcript-directive area.
 *
 * Install: symlink the `desktop/` folder into
 *   $HERMES_HOME/desktop-plugins/abelion-intelligence-ui
 * Use in a reply (alone on its own line):
 *   ::ui{version="1" id="wiz-01" kind="wizard"  title="Rotasi" steps="OpenCode|Hermes|9router"}
 *   ::ui{version="1" id="stat-01" kind="status"  title="Gate" items="Hook:siap|Credential:blocked"}
 *   ::ui{version="1" id="trace-01" kind="trace"   title="Kenapa" steps="Input|Bukti|Keputusan"}
 *   ::ui{version="1" id="cmp-01" kind="compare" title="Opsi" left="A|B" right="C|D" pick="left"}
 *   ::ui{version="1" id="form-01" kind="form"    title="Input" fields="Nama|Catatan" submit="Kirim"}
 *
 * All attrs are untrusted strings. They are capped, never parsed as markup,
 * and rendered as React text children. No network, no privileged API.
 */
import { jsx, jsxs } from 'react/jsx-runtime'
import { useEffect, useState } from 'react'
import { TRANSCRIPT_DIRECTIVE_AREA, host, haptic } from '@hermes/plugin-sdk'

const ID = 'abelion-intelligence-ui'
const VERSION = '1'
const MAX_PROMPT = 240
const MAX_ROW = 60
let uiStorage = null
const KINDS = new Set(['wizard', 'status', 'trace', 'compare', 'form'])

function text(value, max) {
  return typeof value === 'string' ? value.trim().slice(0, max) : ''
}

function items(value, max) {
  if (typeof value !== 'string') return []
  return value
    .split('|')
    .map((part) => text(part, MAX_ROW))
    .filter(Boolean)
    .slice(0, max)
}

function send(prompt, setError, owner) {
  const full = String(prompt)
  if (!full.trim()) return false
  if (full.length > MAX_PROMPT) {
    setError('Permintaan terlalu panjang. Ringkas pilihan Anda lalu coba lagi.')
    return false
  }
  try {
    const focused = host?.state?.focusedSessionId?.get?.() || null
    if (owner && focused && focused !== owner) {
      setError('Kartu ini milik percakapan lain.')
      return false
    }
    const composer = host?.composer
    if (!composer || typeof composer.submit !== 'function') {
      setError('Composer tidak menerima permintaan ini.')
      return false
    }
    const accepted = composer.submit(owner || focused, full)
    setError(accepted ? '' : 'Composer tidak menerima permintaan ini.')
    if (accepted) haptic('tap')
    return Boolean(accepted)
  } catch {
    setError('Composer tidak menerima permintaan ini.')
    return false
  }
}

function Card({ attrs, streaming, sessionId }) {
  const rawKind = text(attrs.kind, 20)
  const version = text(attrs.version, 4) || VERSION
  const kind = rawKind || 'wizard'
  const invalid =
    Boolean(attrs.version && version !== VERSION) ||
    Boolean(rawKind && !KINDS.has(rawKind))
  const cardId = text(attrs.id, 60) || `${version}-${kind}-${text(attrs.title, 20)}`
  const storageKey = `${ID}:${version}:${kind}:${sessionId || 'global'}:${cardId}`
  const rows = items(attrs.steps || attrs.items, 8)
  const persistable = kind === 'wizard' && !invalid && !streaming

  const loadDone = () => {
    if (streaming || invalid || kind !== 'wizard') return []
    try {
      const saved = uiStorage ? uiStorage.get(storageKey) : null
      if (!Array.isArray(saved)) return []
      if (saved.every((x) => typeof x === 'number')) {
        return saved.filter((n) => Number.isInteger(n) && n >= 0 && n < rows.length)
      }
      // Legacy string labels: map to the first unused matching row.
      if (saved.every((x) => typeof x === 'string')) {
        const used = new Set()
        const result = []
        for (const label of saved) {
          const idx = rows.findIndex((r, i) => r === label && !used.has(i))
          if (idx !== -1) {
            used.add(idx)
            result.push(idx)
          }
        }
        return result
      }
      return []
    } catch {
      return []
    }
  }
  const persist = (next) => {
    try {
      if (uiStorage) uiStorage.set(storageKey, next)
    } catch {
      // Persistence is best-effort; local state still works for this mount.
    }
  }
  const [done, setDone] = useState(loadDone)
  const [error, setError] = useState('')
  const [values, setValues] = useState({})
  const [busy, setBusy] = useState(false)
  const [confirmed, setConfirmed] = useState(false)

  // Persist stable row indices, not labels, and only for valid final wizard cards.
  useEffect(() => {
    if (persistable) persist(done)
  }, [storageKey, persistable, done])

  const submit = (prompt) => {
    if (busy) return
    setBusy(true)
    try {
      send(prompt, setError, sessionId || null)
    } finally {
      setBusy(false)
    }
  }
  const toggle = (index) =>
    setDone((prev) => {
      const next = prev.includes(index) ? prev.filter((n) => n !== index) : [...prev, index]
      persist(next) // survive an immediate reload before the effect runs
      return next
    })

  const invalidNode = jsx('div', {
    style: { fontSize: 12, color: 'var(--ui-text-secondary, var(--muted-foreground))' },
    children: 'Kartu UI tidak didukung; menampilkan teks biasa.',
  })
  const streamingNode = jsx('div', {
    style: { fontSize: 12, color: 'var(--ui-text-secondary, var(--muted-foreground))' },
    children: 'Menyiapkan kartu…',
  })

  const shell = {
    maxWidth: 760,
    padding: '12px 2px 10px',
    color: 'var(--foreground)',
    fontSize: 13,
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

  if (invalid) return invalidNode
  if (streaming) return streamingNode

  const title = text(attrs.title, 80) || 'Intelligence UI'
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
                    style: { ...button, opacity: busy ? 0.6 : 1 },
                    disabled: busy,
                    onClick: () => submit(`Bantu: ${title} — ${row}`),
                    children: 'Bantu',
                  }),
                  jsx('button', {
                    type: 'button',
                    style: { ...button, color: 'var(--ui-text-secondary, var(--muted-foreground))' },
                    onClick: () => toggle(index),
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
        style: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 10 },
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
    const submitLabel = text(attrs.submit, 40) || 'Kirim'
    const sensitive = fields.some((field) => /password|token|secret|api.?key|credential|authorization/i.test(field))
    fields.forEach((field, index) =>
      children.push(
        jsxs('label', {
          key: `f${index}`,
          style: { display: 'block', marginTop: 9, ...muted },
          children: [
            jsx('div', { children: field }),
            jsx('input', {
              type: sensitive ? 'password' : 'text',
              value: values[index] || '',
              maxLength: 160,
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
    if (sensitive) {
      children.push(
        jsx('div', { key: 'warn', style: { ...muted, marginTop: 8 }, children:
          'Kartu ini meminta data sensitif. Kirim hanya jika Anda ingin nilai tersebut masuk ke percakapan dan penyedia model.' })
      )
      children.push(
        jsxs('label', { key: 'confirm', style: { ...muted, marginTop: 6, display: 'flex', gap: 6 }, children: [
          jsx('input', { type: 'checkbox', checked: confirmed, onChange: (e) => setConfirmed(e.target.checked) }),
          'Saya mengerti dan ingin mengirim nilai ini.',
        ] })
      )
    }
    children.push(
      jsx('button', {
        key: 'submit',
        type: 'button',
        style: { ...button, marginTop: 10, opacity: busy || (sensitive && !confirmed) ? 0.6 : 1 },
        disabled: busy || (sensitive && !confirmed),
        onClick: () =>
          submit(
            `${title}: ${fields.map((field, index) => `${field}=${values[index] || ''}`).join('; ')}`
          ),
        children: submitLabel,
      })
    )
  } else if (kind === 'trace') {
    const traceChildren = [
      jsx('summary', { key: 'sum', children: `Kenapa — ${rows.length} node` }),
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

  if (error) children.push(jsx('div', { key: 'err', style: { ...muted, marginTop: 8 }, children: error }))

  return jsx('div', { 'data-ui-directive': kind, style: shell, children })
}

export default {
  id: ID,
  name: 'Abelion Intelligence UI',
  register(ctx) {
    uiStorage = ctx.storage || null
    ctx.register({
      id: 'ui.directive',
      area: TRANSCRIPT_DIRECTIVE_AREA,
      data: {
        name: 'ui',
        render: ({ attrs, streaming, sessionId }) => jsx(Card, { attrs: attrs || {}, streaming, sessionId }),
      },
    })
  },
}
