import { formatPct, probLevel } from '../utils/colors'

const MEDALS = ['🥇', '🥈', '🥉']

// Top-5 leaderboard. `entries` are normalized to
// { id, name, flag, wins, probability }.
export default function Leaderboard({ entries = [], title = 'Top 5 — Live', subtitle }) {
  const maxProb = Math.max(0.0001, ...entries.map((e) => e.probability || 0))

  return (
    <div className="rounded-2xl border border-slate-700/60 bg-slate-900/60 p-5 shadow-lg backdrop-blur">
      <div className="mb-3 flex items-baseline justify-between">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{title}</h2>
        {subtitle && <span className="text-[11px] text-slate-500">{subtitle}</span>}
      </div>

      {entries.length === 0 ? (
        <p className="py-6 text-center text-sm text-slate-500">Awaiting first results…</p>
      ) : (
        <ol className="space-y-2">
          {entries.slice(0, 5).map((e, i) => {
            const level = probLevel(e.probability)
            const barPct = ((e.probability || 0) / maxProb) * 100
            return (
              <li
                key={e.id}
                className="animate-fade-in rounded-lg border border-slate-700/50 bg-slate-800/40 p-2.5"
              >
                <div className="flex items-center gap-2.5">
                  <span className="w-6 text-center text-base">{MEDALS[i] || i + 1}</span>
                  <span className="text-xl leading-none">{e.flag}</span>
                  <span className="flex-1 truncate text-sm font-semibold text-slate-100">
                    {e.name}
                  </span>
                  <div className="text-right">
                    <div className="text-sm font-bold tabular-nums text-slate-100">
                      {formatPct(e.probability)}
                    </div>
                    <div className="text-[10px] tabular-nums text-slate-500">
                      {e.wins?.toLocaleString()} wins
                    </div>
                  </div>
                </div>
                <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-slate-700/50">
                  <div
                    className={`h-full rounded-full ${level.bar} transition-[width] duration-300`}
                    style={{ width: `${barPct}%` }}
                  />
                </div>
              </li>
            )
          })}
        </ol>
      )}
    </div>
  )
}
