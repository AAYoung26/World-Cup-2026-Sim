import { formatPct, probLevel } from '../utils/colors'

const ROUND_META = [
  { key: 'ROUND_OF_32', label: 'Round of 32' },
  { key: 'ROUND_OF_16', label: 'Round of 16' },
  { key: 'QUARTER', label: 'Quarterfinals' },
  { key: 'SEMI', label: 'Semifinals' },
  { key: 'FINAL', label: 'Final' },
]

// ESPN-style knockout bracket. The structure is the "chalk" bracket (favorites
// advance); every team cell is coloured by its Monte Carlo championship
// probability, and the top-5 teams get prominent percentage labels.
export default function Bracket({ bracket, topIds = new Set() }) {
  const rounds = bracket?.rounds || {}
  const finalMatch = rounds.FINAL?.[0]
  const champion = finalMatch
    ? finalMatch.winner_id === finalMatch.home?.id
      ? finalMatch.home
      : finalMatch.away
    : null

  return (
    <div className="rounded-2xl border border-slate-700/60 bg-slate-900/60 p-5 shadow-lg backdrop-blur">
      <div className="mb-1 flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">
          Projected Knockout Bracket
        </h2>
        <span className="text-[11px] text-slate-500">
          Favorites advance · cell colour = championship probability
        </span>
      </div>

      <div className="scroll-thin flex items-stretch gap-3 overflow-x-auto pb-3 pt-2">
        {ROUND_META.map((r) => (
          <RoundColumn
            key={r.key}
            label={r.label}
            matches={rounds[r.key] || []}
            topIds={topIds}
          />
        ))}
        <ChampionColumn champion={champion} />
      </div>
    </div>
  )
}

function RoundColumn({ label, matches, topIds }) {
  return (
    <div className="flex min-w-[195px] flex-col">
      <div className="mb-2 rounded-md bg-slate-800/60 py-1 text-center text-[11px] font-bold uppercase tracking-wide text-slate-300">
        {label}
      </div>
      <div className="flex flex-1 flex-col justify-around gap-2">
        {matches.map((m) => (
          <MatchCard key={m.slot} match={m} topIds={topIds} />
        ))}
      </div>
    </div>
  )
}

function MatchCard({ match, topIds }) {
  return (
    <div className="overflow-hidden rounded-lg border border-slate-700/60 bg-slate-800/30 shadow-sm">
      <TeamRow
        team={match.home}
        winner={match.winner_id === match.home?.id}
        topIds={topIds}
      />
      <div className="h-px bg-slate-700/60" />
      <TeamRow
        team={match.away}
        winner={match.winner_id === match.away?.id}
        topIds={topIds}
      />
    </div>
  )
}

function TeamRow({ team, winner, topIds }) {
  if (!team) {
    return <div className="px-2 py-1.5 text-xs italic text-slate-600">TBD</div>
  }
  const level = probLevel(team.championship_probability)
  const isTop = topIds.has(team.id)
  const showPct = team.championship_probability >= 0.005
  return (
    <div
      className={`flex items-center gap-1.5 border-l-4 px-2 py-1.5 ${
        winner ? 'bg-slate-700/40' : 'opacity-60'
      }`}
      style={{ borderLeftColor: level.hex }}
    >
      <span className="text-sm leading-none">{team.flag}</span>
      <span
        className={`flex-1 truncate text-xs ${
          winner ? 'font-bold text-slate-50' : 'font-medium text-slate-300'
        }`}
        title={`${team.name} · Elo ${team.elo_rating}`}
      >
        {team.name}
      </span>
      {winner && <span className="text-[10px] text-emerald-400">✓</span>}
      {showPct && (
        <span
          className="tabular-nums text-[10px] font-semibold"
          style={{ color: isTop ? level.hex : '#64748b' }}
        >
          {formatPct(team.championship_probability, team.championship_probability >= 0.1 ? 0 : 1)}
        </span>
      )}
    </div>
  )
}

function ChampionColumn({ champion }) {
  if (!champion) return null
  return (
    <div className="flex min-w-[170px] flex-col">
      <div className="mb-2 rounded-md bg-amber-500/15 py-1 text-center text-[11px] font-bold uppercase tracking-wide text-amber-300">
        Champion
      </div>
      <div className="flex flex-1 flex-col justify-center">
        <div className="rounded-xl border-2 border-amber-400/70 bg-gradient-to-b from-amber-500/20 to-slate-900/40 p-4 text-center shadow-lg">
          <div className="text-3xl">🏆</div>
          <div className="mt-2 text-3xl leading-none">{champion.flag}</div>
          <div className="mt-1.5 text-sm font-bold text-amber-100">{champion.name}</div>
          <div className="mt-1 text-xs font-semibold text-amber-300">
            {formatPct(champion.championship_probability)} to win it all
          </div>
        </div>
      </div>
    </div>
  )
}
