import { useState } from 'react'

// "Elo Influence" slider: 0% = every match is a coin flip, 100% = full Elo.
export default function EloSlider({ value, onChange, disabled }) {
  const [showTip, setShowTip] = useState(false)
  const fill = `linear-gradient(to right, #22c55e 0%, #22c55e ${value}%, #1e293b ${value}%, #1e293b 100%)`

  return (
    <div className="w-full">
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <label htmlFor="elo-slider" className="text-sm font-semibold text-slate-200">
            Elo Influence
          </label>
          <div className="relative">
            <button
              type="button"
              aria-label="What does Elo Influence do?"
              onMouseEnter={() => setShowTip(true)}
              onMouseLeave={() => setShowTip(false)}
              onFocus={() => setShowTip(true)}
              onBlur={() => setShowTip(false)}
              className="flex h-4 w-4 items-center justify-center rounded-full border border-slate-500 text-[10px] font-bold text-slate-400 hover:text-slate-200"
            >
              ?
            </button>
            {showTip && (
              <div className="absolute left-1/2 z-20 mt-2 w-64 -translate-x-1/2 rounded-lg border border-slate-700 bg-slate-900 p-3 text-xs leading-relaxed text-slate-300 shadow-xl">
                Controls how much team strength (Elo rating) decides match
                outcomes.
                <span className="mt-1 block text-slate-400">
                  <b className="text-slate-200">0%</b> — pure luck, every game is
                  a 50/50 coin flip.
                  <br />
                  <b className="text-slate-200">100%</b> — favorites win at their
                  full Elo-predicted rate.
                </span>
              </div>
            )}
          </div>
        </div>
        <span className="rounded-md bg-emerald-500/15 px-2 py-0.5 text-sm font-bold tabular-nums text-emerald-300">
          {value}%
        </span>
      </div>

      <input
        id="elo-slider"
        type="range"
        min="0"
        max="100"
        step="1"
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(Number(e.target.value))}
        className="elo-slider w-full disabled:opacity-50"
        style={{ background: fill }}
      />

      <div className="mt-1 flex justify-between text-[11px] text-slate-500">
        <span>Pure luck</span>
        <span>Balanced</span>
        <span>Full Elo</span>
      </div>
    </div>
  )
}
