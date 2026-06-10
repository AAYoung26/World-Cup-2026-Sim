import { useEffect, useMemo, useState } from 'react'
import { fetchHealth, fetchTeams } from './api'
import { useSimulation } from './useSimulation'
import ControlPanel from './components/ControlPanel'
import ProgressBar from './components/ProgressBar'
import Leaderboard from './components/Leaderboard'
import ProbabilityChart from './components/ProbabilityChart'
import Bracket from './components/Bracket'
import Legend from './components/Legend'
import { formatPct } from './utils/colors'

export default function App() {
  const [eloWeight, setEloWeight] = useState(100)
  const [numRuns, setNumRuns] = useState(1000)
  const [teams, setTeams] = useState([])
  const [eloSource, setEloSource] = useState(null)
  const [backendError, setBackendError] = useState(null)

  const { status, progress, result, error, reconnecting, run, abort } = useSimulation()

  useEffect(() => {
    let alive = true
    Promise.all([fetchTeams(), fetchHealth().catch(() => null)])
      .then(([t, h]) => {
        if (!alive) return
        setTeams(t)
        setEloSource(h?.elo_source ?? null)
      })
      .catch(() => {
        if (alive)
          setBackendError(
            'Cannot reach the backend at /api. Start it with: uvicorn app.main:app --reload (port 8000).',
          )
      })
    return () => {
      alive = false
    }
  }, [])

  const isBusy = status === 'connecting' || status === 'running'
  const isComplete = status === 'complete' && !!result

  const liveEntries = progress?.top_5_teams || []
  const finalEntries = useMemo(
    () =>
      (result?.teams || []).slice(0, 5).map((t) => ({
        id: t.team_id,
        name: t.name,
        flag: t.flag,
        wins: t.championship_count,
        probability: t.championship_probability,
      })),
    [result],
  )
  const topIds = useMemo(
    () => new Set((result?.teams || []).slice(0, 5).map((t) => t.team_id)),
    [result],
  )

  const leaderboardEntries = isComplete ? finalEntries : liveEntries
  const champion = result?.teams?.[0]

  return (
    <div className="min-h-full">
      <Header teams={teams} eloSource={eloSource} />

      <main className="mx-auto max-w-7xl px-4 pb-16 sm:px-6">
        {backendError && (
          <Banner tone="error" title="Backend unavailable" message={backendError} />
        )}

        <div className="grid grid-cols-1 gap-5 lg:grid-cols-[340px_minmax(0,1fr)]">
          {/* Sidebar */}
          <aside className="flex flex-col gap-5 lg:sticky lg:top-5 lg:self-start">
            <ControlPanel
              eloWeight={eloWeight}
              setEloWeight={setEloWeight}
              numRuns={numRuns}
              setNumRuns={setNumRuns}
              onRun={() => run({ eloWeight, numRuns })}
              onAbort={abort}
              status={status}
              eloSource={eloSource}
            />
            {(isBusy || isComplete) && (
              <Leaderboard
                entries={leaderboardEntries}
                title={isComplete ? 'Final Top 5' : 'Top 5 — Live'}
                subtitle={
                  isComplete
                    ? `${result.runs_completed.toLocaleString()} runs`
                    : 'updating…'
                }
              />
            )}
            <Legend />
          </aside>

          {/* Main content */}
          <section className="flex flex-col gap-5">
            {(isBusy || isComplete || status === 'aborted') && (
              <ProgressBar
                progress={progress}
                status={status}
                reconnecting={reconnecting}
              />
            )}

            {status === 'error' && (
              <Banner tone="error" title="Simulation error" message={error} />
            )}
            {status === 'aborted' && (
              <Banner
                tone="warn"
                title="Simulation aborted"
                message="The live view was stopped. The run may still finish on the server and remain retrievable via the results endpoint."
              />
            )}

            {status === 'idle' && !result && !backendError && <WelcomeCard teams={teams} />}

            {isComplete && (
              <>
                <ResultsSummary result={result} champion={champion} />
                <Bracket bracket={result.bracket} topIds={topIds} />
                <ProbabilityChart teams={result.teams} topN={10} />
              </>
            )}
          </section>
        </div>

        <Footer />
      </main>
    </div>
  )
}

function Header({ teams, eloSource }) {
  return (
    <header className="border-b border-slate-800/80 bg-slate-950/40">
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight text-white sm:text-3xl">
              <span className="text-emerald-400">⚽ World Cup 2026</span> Simulator
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              Monte Carlo tournament forecasting · 48 teams · live championship odds
            </p>
          </div>
          <div className="flex gap-2 text-center">
            <Stat label="Teams" value={teams.length || 48} />
            <Stat label="Groups" value="12" />
            <Stat
              label="Elo source"
              value={eloSource ? eloSource : '—'}
            />
          </div>
        </div>
      </div>
    </header>
  )
}

function Stat({ label, value }) {
  return (
    <div className="rounded-xl border border-slate-700/60 bg-slate-900/60 px-3 py-1.5">
      <div className="text-base font-bold leading-none text-slate-100">{value}</div>
      <div className="mt-0.5 text-[10px] uppercase tracking-wide text-slate-500">{label}</div>
    </div>
  )
}

function ResultsSummary({ result, champion }) {
  return (
    <div className="rounded-2xl border border-emerald-700/40 bg-gradient-to-r from-emerald-900/30 to-slate-900/40 p-5 shadow-lg">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-emerald-400">
            Most likely champion
          </p>
          {champion && (
            <p className="mt-1 text-2xl font-extrabold text-white">
              {champion.flag} {champion.name}{' '}
              <span className="text-emerald-300">
                {formatPct(champion.championship_probability)}
              </span>
            </p>
          )}
        </div>
        <div className="flex gap-2 text-center text-xs">
          <SummaryStat label="Runs" value={result.runs_completed.toLocaleString()} />
          <SummaryStat label="Elo weight" value={`${result.elo_weight.toFixed(0)}%`} />
          <SummaryStat label="Compute" value={`${result.duration_seconds}s`} />
        </div>
      </div>
    </div>
  )
}

function SummaryStat({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-700/50 bg-slate-900/50 px-3 py-2">
      <div className="text-base font-bold tabular-nums text-slate-100">{value}</div>
      <div className="text-[10px] uppercase tracking-wide text-slate-500">{label}</div>
    </div>
  )
}

function WelcomeCard({ teams }) {
  return (
    <div className="rounded-2xl border border-slate-700/60 bg-slate-900/60 p-8 text-center shadow-lg">
      <div className="text-5xl">🏆</div>
      <h2 className="mt-3 text-xl font-bold text-white">Forecast the 2026 World Cup</h2>
      <p className="mx-auto mt-2 max-w-md text-sm text-slate-400">
        Adjust the <b className="text-slate-200">Elo Influence</b> slider, pick how
        many simulations to run, and hit{' '}
        <b className="text-emerald-300">Run Simulation</b>. Watch the live leaderboard
        update over a WebSocket, then explore the projected bracket and each team's
        championship probability.
      </p>
      {teams.length > 0 && (
        <p className="mt-4 text-xs text-slate-500">
          {teams.length} teams loaded across 12 groups · ready to simulate
        </p>
      )}
    </div>
  )
}

function Banner({ tone = 'error', title, message }) {
  const tones = {
    error: 'border-rose-700/50 bg-rose-900/30 text-rose-200',
    warn: 'border-amber-700/50 bg-amber-900/30 text-amber-200',
  }
  return (
    <div className={`rounded-xl border p-4 ${tones[tone]}`}>
      <p className="text-sm font-bold">{title}</p>
      {message && <p className="mt-1 text-xs opacity-90">{message}</p>}
    </div>
  )
}

function Footer() {
  return (
    <p className="mt-10 text-center text-xs text-slate-600">
      Probabilities are Monte Carlo estimates from a logistic Elo model · group
      assignments are representative of the 2026 format.
    </p>
  )
}
