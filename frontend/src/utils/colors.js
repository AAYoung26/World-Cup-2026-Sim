// Championship-probability colour scale.
//
// The spec calls for five distinct confidence levels:
//   <5%, 5-15%, 15-30%, 30-50%, >50%
// Each level maps to a colour used consistently across the bracket, the
// leaderboard, the chart and the legend.

export const PROB_LEVELS = [
  {
    id: 0,
    label: 'Long shot',
    range: '< 5%',
    threshold: 0.05,
    hex: '#64748b', // slate-500
    bg: 'bg-slate-800/70',
    border: 'border-slate-600',
    text: 'text-slate-300',
    chip: 'bg-slate-600/30 text-slate-300 border border-slate-500/40',
    bar: 'bg-slate-500',
  },
  {
    id: 1,
    label: 'Outside bet',
    range: '5–15%',
    threshold: 0.15,
    hex: '#0ea5e9', // sky-500
    bg: 'bg-sky-900/40',
    border: 'border-sky-500/70',
    text: 'text-sky-200',
    chip: 'bg-sky-500/20 text-sky-200 border border-sky-400/40',
    bar: 'bg-sky-500',
  },
  {
    id: 2,
    label: 'Contender',
    range: '15–30%',
    threshold: 0.3,
    hex: '#10b981', // emerald-500
    bg: 'bg-emerald-900/40',
    border: 'border-emerald-500/70',
    text: 'text-emerald-200',
    chip: 'bg-emerald-500/20 text-emerald-200 border border-emerald-400/40',
    bar: 'bg-emerald-500',
  },
  {
    id: 3,
    label: 'Favorite',
    range: '30–50%',
    threshold: 0.5,
    hex: '#f59e0b', // amber-500
    bg: 'bg-amber-900/40',
    border: 'border-amber-500/70',
    text: 'text-amber-200',
    chip: 'bg-amber-500/20 text-amber-200 border border-amber-400/40',
    bar: 'bg-amber-500',
  },
  {
    id: 4,
    label: 'Heavy favorite',
    range: '> 50%',
    threshold: 1.01,
    hex: '#f43f5e', // rose-500
    bg: 'bg-rose-900/40',
    border: 'border-rose-500/80',
    text: 'text-rose-200',
    chip: 'bg-rose-500/20 text-rose-200 border border-rose-400/40',
    bar: 'bg-rose-500',
  },
]

// Return the level descriptor for a probability in [0, 1].
export function probLevel(prob) {
  const p = prob ?? 0
  for (const level of PROB_LEVELS) {
    if (p < level.threshold) return level
  }
  return PROB_LEVELS[PROB_LEVELS.length - 1]
}

export function probColor(prob) {
  return probLevel(prob).hex
}

export function formatPct(prob, digits = 1) {
  return `${((prob ?? 0) * 100).toFixed(digits)}%`
}
