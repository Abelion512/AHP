/**
 * Interview and quiz cards for the Aero `ui` directive (kinds `interview`, `quiz`).
 *
 * Data only: every attribute is an untrusted, length-capped string rendered as
 * React text. No markup, no URLs, no network, no script. The interview submits
 * through the owning chat composer (same path as `choice`); the quiz is local
 * state only, like `flow` and `chart`.
 *
 * interview: groups="Label A|Label B"  g1_options="Title::Explanation|Title::Explanation"
 *            g2_options=...  submit="Simpan keputusan"
 * quiz:      questions="Q1|Q2"  q1_options="A|B|C|D"  q1_answer="B"  q1_explain="Why"
 */
import { createElement as h, useState } from 'react'

const MAX_RAW = 2048

function clean(value, max) {
  return typeof value === 'string' ? value.trim().slice(0, max) : ''
}

function split(raw, minCount, maxCount, maxLen) {
  if (typeof raw !== 'string' || raw.length > MAX_RAW) return null
  const parts = raw.split('|').map(v => v.trim())
  if (parts.length < minCount || parts.length > maxCount || parts.some(v => !v || v.length > maxLen)) return null
  return parts
}

export function normalizeInterview(attrs) {
  const labels = split(attrs.groups, 1, 4, 80)
  if (!labels) return { error: 'Data wawancara tidak valid. Gunakan jawaban teks.' }
  const groups = []
  for (let i = 0; i < labels.length; i += 1) {
    const rows = split(attrs[`g${i + 1}_options`], 2, 6, 260)
    if (!rows) return { error: 'Pilihan wawancara tidak valid. Gunakan jawaban teks.' }
    const options = rows.map(row => {
      const at = row.indexOf('::')
      return at < 0 ? { title: row, desc: '' } : { title: row.slice(0, at).trim(), desc: row.slice(at + 2).trim() }
    })
    if (options.some(o => !o.title || o.title.length > 60 || o.desc.length > 180)) {
      return { error: 'Pilihan wawancara terlalu panjang. Gunakan jawaban teks.' }
    }
    if (new Set(options.map(o => o.title)).size !== options.length) return { error: 'Pilihan harus berbeda.' }
    groups.push({ label: labels[i], options })
  }
  return { kind: 'interview', groups, submit: clean(attrs.submit, 40) || 'Simpan keputusan' }
}

export function normalizeQuiz(attrs) {
  const texts = split(attrs.questions, 1, 5, 160)
  if (!texts) return { error: 'Data kuis tidak valid. Gunakan jawaban teks.' }
  const questions = []
  for (let i = 0; i < texts.length; i += 1) {
    const options = split(attrs[`q${i + 1}_options`], 2, 4, 80)
    const letter = clean(attrs[`q${i + 1}_answer`], 1).toUpperCase()
    const answer = 'ABCD'.indexOf(letter)
    if (!options || !letter || answer < 0 || answer >= options.length) return { error: 'Kunci kuis tidak valid. Gunakan jawaban teks.' }
    if (new Set(options).size !== options.length) return { error: 'Pilihan harus berbeda.' }
    questions.push({ q: texts[i], options, answer, explain: clean(attrs[`q${i + 1}_explain`], 180) })
  }
  return { kind: 'quiz', questions }
}

export const formsCss = `
.aero-int{border:1px solid color-mix(in srgb,currentColor 12%,transparent);border-radius:12px;padding:12px;margin:10px 0}
.aero-int fieldset{border:0;margin:0;padding:0;min-width:0}
.aero-int fieldset+fieldset{border-top:1px solid color-mix(in srgb,currentColor 12%,transparent);margin-top:12px;padding-top:12px}
.aero-int legend{font-size:15px;font-weight:600;padding:0;margin:0 0 6px}
.aero-int label{display:grid;grid-template-columns:20px minmax(0,1fr) minmax(0,2fr);gap:4px 10px;align-items:start;padding:8px 0;cursor:pointer;min-height:44px}
.aero-int label>span:first-of-type{font-weight:600}
.aero-int label>span+span{opacity:.82}
.aero-int input[type=radio]{margin:3px 0 0;accent-color:#111}
.aero-int button{width:100%;min-height:44px;border:0;border-radius:9999px;background:#111;color:#fff;font:inherit;font-size:14px;font-weight:500;cursor:pointer;margin-top:12px}
.aero-int button:disabled{opacity:.4;cursor:default}
@container (max-width:520px){.aero-int label{grid-template-columns:20px minmax(0,1fr)}.aero-int label>span+span{grid-column:2}}
.aero-quiz{border:1px solid color-mix(in srgb,currentColor 12%,transparent);border-radius:14px;padding:12px;margin:10px 0}
.aero-quiz-head{display:flex;justify-content:space-between;gap:8px;font-size:12px;opacity:.75;margin-bottom:6px}
.aero-quiz-q{font-size:15px;font-weight:600;margin:4px 0 10px}
.aero-quiz-opt{display:flex;align-items:center;gap:10px;width:100%;text-align:left;font:inherit;color:inherit;background:transparent;border:1px solid transparent;border-radius:12px;padding:8px;min-height:44px;cursor:pointer}
.aero-quiz-opt:hover:not(:disabled){background:color-mix(in srgb,currentColor 6%,transparent)}
.aero-quiz-opt:disabled{cursor:default}
.aero-quiz-badge{flex:0 0 28px;height:28px;border-radius:99px;border:1px solid color-mix(in srgb,currentColor 25%,transparent);display:grid;place-items:center;font-size:12px;font-weight:600}
.aero-quiz-opt[data-state=correct]{background:color-mix(in srgb,#16a34a 16%,transparent);border-color:#16a34a}
.aero-quiz-opt[data-state=wrong]{background:color-mix(in srgb,#dc2626 14%,transparent);border-color:#dc2626}
.aero-quiz-opt[data-state=correct] .aero-quiz-badge{background:#16a34a;color:#fff;border-color:#16a34a}
.aero-quiz-opt[data-state=wrong] .aero-quiz-badge{background:#dc2626;color:#fff;border-color:#dc2626}
.aero-quiz-tag{margin-left:auto;font-size:12px;font-weight:600}
.aero-quiz-note{margin:10px 0 0;padding:10px;border-radius:10px;background:color-mix(in srgb,currentColor 6%,transparent);font-size:13px;line-height:1.5}
.aero-quiz-next{margin-top:12px;min-height:40px;padding:8px 16px;border-radius:9999px;border:1px solid color-mix(in srgb,currentColor 25%,transparent);background:transparent;color:inherit;font:inherit;font-size:13px;cursor:pointer}
.aero-quiz-next:disabled{opacity:.4;cursor:default}
`

export function InterviewView({ model, title, owner, send, setError }) {
  const [picked, setPicked] = useState({})
  const ready = model.groups.every((_, i) => Number.isInteger(picked[i]))
  const submit = () => {
    if (!ready) return
    const parts = model.groups.map((g, i) => `${g.label}: ${g.options[picked[i]].title}`)
    send(owner, `Jawaban: ${title} - ${parts.join('; ')}`, setError)
  }
  return h('div', { className: 'aero-int', role: 'group', 'aria-label': title }, h('style', null, formsCss),
    ...model.groups.map((g, gi) => h('fieldset', { key: gi },
      h('legend', null, g.label),
      ...g.options.map((o, oi) => h('label', { key: oi },
        h('input', { type: 'radio', name: `aero-int-${gi}`, checked: picked[gi] === oi, onChange: () => setPicked(p => ({ ...p, [gi]: oi })) }),
        h('span', null, o.title),
        o.desc ? h('span', null, o.desc) : null)))),
    h('button', { type: 'button', disabled: !owner || !ready, onClick: submit }, model.submit))
}

export function QuizView({ model, title }) {
  const total = model.questions.length
  const [index, setIndex] = useState(0)
  const [picks, setPicks] = useState([])
  const done = index >= total
  const style = h('style', null, formsCss)
  if (done) {
    const score = model.questions.reduce((n, q, i) => n + (picks[i] === q.answer ? 1 : 0), 0)
    return h('div', { className: 'aero-quiz', role: 'status' }, style,
      h('div', { className: 'aero-quiz-q' }, `Skor ${score} dari ${total}`),
      ...model.questions.map((q, i) => h('div', { key: i, style: { padding: '4px 0', fontSize: 13 } },
        `${picks[i] === q.answer ? '\u2713' : '\u2717'} ${q.q}`)),
      h('button', { type: 'button', className: 'aero-quiz-next', onClick: () => { setIndex(0); setPicks([]) } }, 'Ulangi'))
  }
  const q = model.questions[index]
  const chosen = picks[index]
  const answered = Number.isInteger(chosen)
  return h('div', { className: 'aero-quiz', role: 'group', 'aria-label': title }, style,
    h('div', { className: 'aero-quiz-head' }, h('span', null, `Soal ${index + 1} dari ${total}`), h('span', null, title)),
    h('div', { className: 'aero-quiz-q' }, q.q),
    ...q.options.map((o, oi) => {
      const state = !answered ? 'idle' : oi === q.answer ? 'correct' : oi === chosen ? 'wrong' : 'idle'
      return h('button', {
        key: oi, type: 'button', className: 'aero-quiz-opt', 'data-state': state, disabled: answered, 'aria-pressed': chosen === oi,
        onClick: () => setPicks(p => { const next = p.slice(); next[index] = oi; return next }),
      }, h('span', { className: 'aero-quiz-badge' }, 'ABCD'[oi]), h('span', null, o),
      state === 'correct' ? h('span', { className: 'aero-quiz-tag' }, 'Jawaban benar') : state === 'wrong' ? h('span', { className: 'aero-quiz-tag' }, 'Pilihanmu') : null)
    }),
    answered && q.explain ? h('div', { className: 'aero-quiz-note', role: 'status' }, q.explain) : null,
    h('button', { type: 'button', className: 'aero-quiz-next', disabled: !answered, onClick: () => setIndex(index + 1) }, index + 1 === total ? 'Lihat skor' : 'Berikutnya'))
}
