import { formatPct } from '../utils/colors'
import { advanceTier } from '../utils/predict'

// Predicted finishing order for all 12 groups, from the Monte Carlo runs.
export default function GroupStandings({ groups = [] }) {
  if (groups.length === 0) return null
  return (
    <div className="rounded-2xl border border-slate-700/60 bg-slate-900/60 p-5 shadow-lg backdrop-blur">
      <div className="mb-1 flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">
          Predicted Group Finish
        </h2>
        <span className="text-[11px] text-slate-500">
          Ordered by expected finish · % = chance of reaching the knockouts
        </span>
      </div>

      <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {groups.map((group) => (
          <GroupCard key={group.group} group={group} />
        ))}
      </div>
    </div>
  )
}

function GroupCard({ group }) {
  return (
    <div className="rounded-xl border border-slate-700/60 bg-slate-800/30 p-3">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-xs font-bold uppercase tracking-wide text-slate-300">
          Group {group.group}
        </h3>
        <span className="text-[10px] text-slate-500">advance</span>
      </div>
      <ol className="space-y-1.5">
        {group.teams.map((team, idx) => {
          const tier = advanceTier(team.advance_probability)
          const winProb = team.finish_probs?.[0] ?? 0
          // First two slots are the automatic-qualification positions.
          const autoSpot = idx < 2
          return (
            <li key={team.team_id} className="flex items-center gap-2">
              <span
                className={`flex h-5 w-5 flex-none items-center justify-center rounded text-[11px] font-bold ${
                  autoSpot
                    ? 'bg-emerald-500/20 text-emerald-300'
                    : idx === 2
                      ? 'bg-amber-500/15 text-amber-300'
                      : 'bg-slate-700/40 text-slate-500'
                }`}
              >
                {idx + 1}
              </span>
              <span className="text-base leading-none">{team.flag}</span>
              <div className="min-w-0 flex-1">
                <div className="flex items-baseline justify-between gap-2">
                  <span
                    className="truncate text-xs font-semibold text-slate-100"
                    title={`${team.name} · Elo ${team.elo_rating} · wins group ${formatPct(winProb)}`}
                  >
                    {team.name}
                  </span>
                  <span className={`flex-none text-[11px] font-bold tabular-nums ${tier.text}`}>
                    {formatPct(team.advance_probability, 0)}
                  </span>
                </div>
                <div className="mt-1 h-1 w-full overflow-hidden rounded-full bg-slate-700/50">
                  <div
                    className={`h-full rounded-full ${tier.bar}`}
                    style={{ width: `${Math.max(2, team.advance_probability * 100)}%` }}
                  />
                </div>
              </div>
            </li>
          )
        })}
      </ol>
    </div>
  )
}
