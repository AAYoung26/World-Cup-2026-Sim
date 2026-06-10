import { PROB_LEVELS } from '../utils/colors'

// Colour-key for the five championship-probability confidence levels.
export default function Legend() {
  return (
    <div className="rounded-2xl border border-slate-700/60 bg-slate-900/60 p-4 shadow-lg backdrop-blur">
      <h2 className="mb-3 text-sm font-bold uppercase tracking-wider text-slate-400">
        Championship probability
      </h2>
      <div className="flex flex-wrap gap-2">
        {PROB_LEVELS.map((level) => (
          <div
            key={level.id}
            className="flex items-center gap-2 rounded-lg border border-slate-700/50 bg-slate-800/40 px-2.5 py-1.5"
          >
            <span
              className="h-3 w-3 rounded-sm"
              style={{ backgroundColor: level.hex }}
            />
            <span className="text-xs font-semibold text-slate-200">{level.range}</span>
            <span className="text-[11px] text-slate-500">{level.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
