import EloSlider from './EloSlider'

const RUN_OPTIONS = [1000, 5000, 10000]

// Simulation controls: Elo slider, run-count selector, and run/abort buttons.
export default function ControlPanel({
  eloWeight,
  setEloWeight,
  numRuns,
  setNumRuns,
  onRun,
  onAbort,
  status,
  eloSource,
}) {
  const busy = status === 'connecting' || status === 'running'

  return (
    <div className="rounded-2xl border border-slate-700/60 bg-slate-900/60 p-5 shadow-lg backdrop-blur">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">
          Simulation Controls
        </h2>
        {eloSource && (
          <span
            className="rounded-full border border-slate-600 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-400"
            title={
              eloSource === 'api'
                ? 'Elo ratings loaded from the external API'
                : 'Using bundled fallback Elo ratings'
            }
          >
            Elo: {eloSource}
          </span>
        )}
      </div>

      <EloSlider value={eloWeight} onChange={setEloWeight} disabled={busy} />

      <div className="mt-5">
        <p className="mb-2 text-sm font-semibold text-slate-200">Simulation runs</p>
        <div className="grid grid-cols-3 gap-2">
          {RUN_OPTIONS.map((opt) => (
            <button
              key={opt}
              type="button"
              disabled={busy}
              onClick={() => setNumRuns(opt)}
              className={`rounded-lg border px-3 py-2 text-sm font-semibold tabular-nums transition disabled:opacity-50 ${
                numRuns === opt
                  ? 'border-emerald-500 bg-emerald-500/15 text-emerald-200'
                  : 'border-slate-700 bg-slate-800/60 text-slate-300 hover:border-slate-500'
              }`}
            >
              {opt.toLocaleString()}
            </button>
          ))}
        </div>
        <p className="mt-1.5 text-[11px] text-slate-500">
          More runs → smoother probabilities (1,000 runs ≈ a fraction of a second).
        </p>
      </div>

      <div className="mt-5 flex gap-2">
        {busy ? (
          <button
            type="button"
            onClick={onAbort}
            className="flex-1 rounded-lg border border-rose-500/60 bg-rose-500/10 px-4 py-2.5 text-sm font-bold text-rose-200 transition hover:bg-rose-500/20"
          >
            ■ Abort
          </button>
        ) : (
          <button
            type="button"
            onClick={onRun}
            className="flex-1 rounded-lg bg-gradient-to-r from-emerald-500 to-green-600 px-4 py-2.5 text-sm font-bold text-white shadow-md transition hover:from-emerald-400 hover:to-green-500 active:scale-[0.99]"
          >
            ▶ Run Simulation
          </button>
        )}
      </div>
    </div>
  )
}
