// Frontend mirror of the backend's win-probability model, used for the
// head-to-head explorer and projected paths. Kept identical to
// backend/app/probability.py so the UI's "who would they beat" matches the sim.

export function eloWinProb(eloA, eloB) {
  return 1 / (1 + 10 ** ((eloB - eloA) / 400))
}

// weight01 in [0, 1]: 0 -> 50/50, 1 -> full Elo.
export function weightedWinProb(eloA, eloB, weight01) {
  const w = Math.max(0, Math.min(1, weight01))
  const base = eloWinProb(eloA, eloB)
  return 0.5 + w * (base - 0.5)
}

// Knockout rounds in advancement order, plus display labels.
export const KO_ROUND_ORDER = [
  'ROUND_OF_32',
  'ROUND_OF_16',
  'QUARTER',
  'SEMI',
  'FINAL',
]

export const STAGE_LABEL = {
  GROUP: 'Group stage',
  ROUND_OF_32: 'Round of 32',
  ROUND_OF_16: 'Round of 16',
  QUARTER: 'Quarterfinal',
  SEMI: 'Semifinal',
  FINAL: 'Final',
  WINNER: 'Champion',
}

const ORDINAL = ['1st', '2nd', '3rd', '4th']
export function ordinal(position1Indexed) {
  return ORDINAL[position1Indexed - 1] || `${position1Indexed}th`
}

// Trace a team's chalk-bracket path: the opponents it would face round by round
// until it is eliminated (or wins it all). Returns [] if the team did not
// qualify for the knockouts in the projected bracket.
export function buildKnockoutPath(bracket, teamId) {
  const steps = []
  for (const stage of KO_ROUND_ORDER) {
    const matches = bracket?.rounds?.[stage] || []
    const match = matches.find(
      (m) => m.home?.id === teamId || m.away?.id === teamId,
    )
    if (!match) break
    const isHome = match.home?.id === teamId
    const opponent = isHome ? match.away : match.home
    const winProb = isHome
      ? match.home_win_probability
      : 1 - match.home_win_probability
    const won = match.winner_id === teamId
    steps.push({ stage, opponent, winProb, won })
    if (!won) break // eliminated at this round
  }
  return steps
}

// Advancement colour tiers for the group view (distinct from championship
// probability, since "advancing from a group" is a different, higher-base bar).
export function advanceTier(prob) {
  if (prob >= 0.66) return { hex: '#10b981', bar: 'bg-emerald-500', text: 'text-emerald-300' }
  if (prob >= 0.33) return { hex: '#f59e0b', bar: 'bg-amber-500', text: 'text-amber-300' }
  return { hex: '#64748b', bar: 'bg-slate-500', text: 'text-slate-400' }
}
