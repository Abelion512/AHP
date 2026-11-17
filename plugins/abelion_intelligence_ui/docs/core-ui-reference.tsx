// REFERENCE ONLY — NOT APPLIED, NOT IMPORTED, NOT COMPILED.
// Sketch of the core-side alternative to `abelion-intelligence-ui`.
// See docs/CORE_COMPARISON.md for why this is not the chosen surface.

import { jsx } from 'react/jsx-runtime'
import { TRANSCRIPT_DIRECTIVE_AREA } from '@/lib/transcript-directives'

function CoreUiCard({ attrs }: { attrs: Record<string, string> }) {
  const kind = attrs.kind ?? 'wizard'
  const title = (attrs.title ?? '').slice(0, 80)
  const rows = (attrs.steps ?? attrs.items ?? '').split('|').filter(Boolean).slice(0, 8)

  return jsx('div', {
    className: 'max-w-[760px] py-3 text-sm text-foreground',
    children: [
      jsx('div', { key: 'title', className: 'font-medium', children: title }),
      ...rows.map((row, i) =>
        jsx('div', {
          key: i,
          className: 'border-t border-stroke-secondary py-2',
          children: row,
        })
      ),
    ],
  })
}

export const coreUiContribution = {
  id: 'transcript.ui',
  area: TRANSCRIPT_DIRECTIVE_AREA,
  data: {
    name: 'ui',
    render: ({ attrs }: { attrs: Record<string, string> }) => jsx(CoreUiCard, { attrs }),
  },
}
