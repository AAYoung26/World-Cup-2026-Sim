// Live progress bar driven by WebSocket progress messages.
export default function ProgressBar({ progress, status, reconnecting }) {
  const done = progress?.runs_completed ?? 0
  const total = progress?.total_runs ?? 0
  const pct = total > 0 ? Math.min(100, (done / total) * 100) : 0
  const complete = status === 'complete'
  const running = status === 'running' || status === 'connecting'

  return (
    <div className="rounded-2xl border border-slate-700/60 bg-slate-900/60 p-5 shadow-lg backdrop-blur">
      <div className="mb-2 flex items-end justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">
            Progress
          </h2>
          {reconnecting && (
            <span className="animate-pulse rounded-full bg-amber-500/20 px-2 py-0.5 text-[10px] font-semibold text-amber-300">
              reconnecting…
            </span>
          )}
        </div>
        <span className="text-sm font-bold tabular-nums text-slate-200">
          {done.toLocaleString()}
          <span className="text-slate-500"> / {total.toLocaleString()} runs</span>
        </span>
      </div>

      <div className="relative h-4 w-full overflow-hidden rounded-full bg-slate-800">
        <div
          className={`h-full rounded-full transition-[width] duration-300 ease-out ${
            complete
              ? 'bg-gradient-to-r from-emerald-500 to-green-400'
              : 'bg-gradient-to-r from-sky-500 to-emerald-500'
          }`}
          style={{ width: `${pct}%` }}
        >
          {running && pct > 0 && pct < 100 && (
            <div className="relative h-full w-full overflow-hidden">
              <div className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-white/25 to-transparent" />
            </div>
          )}
        </div>
      </div>

      <div className="mt-1.5 flex justify-between text-[11px]">
        <span className="text-slate-500">
          {status === 'connecting' && 'Connecting…'}
          {status === 'running' && 'Simulating tournaments…'}
          {status === 'complete' && 'Simulation complete'}
          {status === 'aborted' && 'Aborted'}
        </span>
        <span className="font-semibold tabular-nums text-slate-300">{pct.toFixed(0)}%</span>
      </div>
    </div>
  )
}
