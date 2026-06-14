import { useMemo, useState } from 'react'
import { formatPct } from '../utils/colors'
import {
  STAGE_LABEL,
  buildKnockoutPath,
  ordinal,
  weightedWinProb,
} from '../utils/predict'

// Pick a team and see who it would beat / lose to, plus its projected path.
export default function TeamExplorer({ teams = [], groups = [], bracket, eloWeight = 100 }) {
  const byId = useMemo(() => {
    const m = {}
    for (const t of teams) m[t.team_id] = t
    return m
  }, [teams])

  const [selectedId, setSelectedId] = useState(teams[0]?.team_id)
  const selected = byId[selectedId] || teams[0]
  const w01 = eloWeight / 100

  const { wins, losses } = useMemo(() => {
    if (!selected) return { wins: [], losses: [] }
    const wins = []
    const losses = []
    for (const o of teams) {
      if (o.team_id === selected.team_id) continue
      const p = weightedWinProb(selected.elo_rating, o.elo_rating, w01)
      const row = { team: o, prob: p }
      if (p >= 0.5) wins.push(row)
      else losses.push(row)
    }
    wins.sort((a, b) => b.prob - a.prob) // most dominant wins first
    losses.sort((a, b) => a.prob - b.prob) // most likely losses first
    return { wins, losses }
  }, [selected, teams, w01])

  const groupInfo = useMemo(() => {
    for (const g of groups) {
      const idx = g.teams.findIndex((t) => t.team_id === selectedId)
      if (idx >= 0) return { group: g, position: idx + 1, entry: g.teams[idx] }
    }
    return null
  }, [groups, selectedId])

  const path = useMemo(() => buildKnockoutPath(bracket, selectedId), [bracket, selectedId])

  if (!selected) return null

  return (
    <div className="rounded-2xl border border-slate-700/60 bg-slate-900/60 p-5 shadow-lg backdrop-blur">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">
          Team Explorer
        </h2>
        <label className="flex items-center gap-2 text-xs text-slate-400">
          Pick a team
          <select
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
            className="rounded-lg border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm font-semibold text-slate-100 outline-none focus:border-emerald-500"
          >
            {teams.map((t) => (
              <option key={t.team_id} value={t.team_id}>
                {t.flag} {t.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      {/* Selected team summary */}
      <div className="mb-4 flex flex-wrap items-center gap-x-6 gap-y-2 rounded-xl border border-slate-700/50 bg-slate-800/40 p-4">
        <div className="flex items-center gap-3">
          <span className="text-4xl leading-none">{selected.flag}</span>
          <div>
            <div className="text-lg font-bold text-white">{selected.name}</div>
            <div className="text-xs text-slate-400">
              Group {selected.group} · Elo {selected.elo_rating}
            </div>
          </div>
        </div>
        <SummaryPill label="Win title" value={formatPct(selected.championship_probability)} />
        {groupInfo && (
          <SummaryPill
            label="Predicted group"
            value={`${ordinal(groupInfo.position)} · ${formatPct(groupInfo.entry.advance_probability, 0)} adv`}
          />
        )}
        <SummaryPill
          label="Would beat / lose to"
          value={`${wins.length} / ${losses.length}`}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ProjectedPath selected={selected} groupInfo={groupInfo} path={path} byId={byId} w01={w01} />
        <HeadToHead wins={wins} losses={losses} />
      </div>
    </div>
  )
}

function SummaryPill({ label, value }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wide text-slate-500">{label}</div>
      <div className="text-sm font-bold text-slate-100">{value}</div>
    </div>
  )
}

function ProjectedPath({ selected, groupInfo, path, byId, w01 }) {
  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-4">
      <h3 className="mb-3 text-xs font-bold uppercase tracking-wide text-slate-300">
        Projected path
      </h3>

      {/* Group opponents */}
      <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
        Group {selected.group}
      </p>
      <div className="space-y-1.5">
        {(groupInfo?.group.teams || [])
          .filter((t) => t.team_id !== selected.team_id)
          .map((opp) => {
            const p = weightedWinProb(selected.elo_rating, opp.elo_rating, w01)
            return <OpponentRow key={opp.team_id} flag={opp.flag} name={opp.name} prob={p} />
          })}
      </div>

      {/* Knockout path */}
      <p className="mb-1 mt-3 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
        Knockout route
      </p>
      {path.length === 0 ? (
        <p className="rounded-lg bg-slate-900/40 px-3 py-2 text-xs text-slate-400">
          Projected to exit in the group stage — doesn't reach the knockouts in the
          favorites bracket.
        </p>
      ) : (
        <div className="space-y-1.5">
          {path.map((step) => (
            <div
              key={step.stage}
              className="flex items-center gap-2 rounded-lg bg-slate-900/30 px-2.5 py-1.5"
            >
              <span className="w-24 flex-none text-[11px] font-semibold text-slate-400">
                {STAGE_LABEL[step.stage]}
              </span>
              <span className="text-sm leading-none">{step.opponent?.flag}</span>
              <span className="flex-1 truncate text-xs text-slate-200">
                {step.opponent?.name}
              </span>
              <span className="text-[11px] font-bold tabular-nums text-slate-300">
                {formatPct(step.winProb, 0)}
              </span>
              <span
                className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${
                  step.won
                    ? 'bg-emerald-500/20 text-emerald-300'
                    : 'bg-rose-500/20 text-rose-300'
                }`}
              >
                {step.won ? 'WIN' : 'OUT'}
              </span>
            </div>
          ))}
          {path.length > 0 && path[path.length - 1].stage === 'FINAL' && path[path.length - 1].won && (
            <div className="rounded-lg bg-amber-500/15 px-3 py-2 text-center text-xs font-bold text-amber-300">
              🏆 Projected champion
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function OpponentRow({ flag, name, prob }) {
  const win = prob >= 0.5
  return (
    <div className="flex items-center gap-2 rounded-lg bg-slate-900/30 px-2.5 py-1.5">
      <span className="text-sm leading-none">{flag}</span>
      <span className="flex-1 truncate text-xs text-slate-200">{name}</span>
      <span className="text-[11px] font-bold tabular-nums text-slate-300">
        {formatPct(prob, 0)}
      </span>
      <span
        className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${
          win ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
        }`}
      >
        {win ? 'WIN' : 'LOSS'}
      </span>
    </div>
  )
}

function HeadToHead({ wins, losses }) {
  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-4">
      <h3 className="mb-3 text-xs font-bold uppercase tracking-wide text-slate-300">
        Head-to-head vs every team
      </h3>
      <div className="grid grid-cols-2 gap-3">
        <H2HColumn title="Would beat" tone="win" rows={wins} />
        <H2HColumn title="Would lose to" tone="loss" rows={losses} />
      </div>
    </div>
  )
}

function H2HColumn({ title, tone, rows }) {
  const win = tone === 'win'
  return (
    <div>
      <div
        className={`mb-1.5 flex items-center justify-between text-[11px] font-bold uppercase tracking-wide ${
          win ? 'text-emerald-300' : 'text-rose-300'
        }`}
      >
        <span>{title}</span>
        <span className="tabular-nums">{rows.length}</span>
      </div>
      <div className="scroll-thin max-h-72 space-y-1 overflow-y-auto pr-1">
        {rows.map(({ team, prob }) => (
          <div
            key={team.team_id}
            className="flex items-center gap-1.5 rounded-md bg-slate-900/30 px-2 py-1"
          >
            <span className="text-xs leading-none">{team.flag}</span>
            <span className="flex-1 truncate text-[11px] text-slate-300">{team.name}</span>
            <span
              className={`text-[10px] font-bold tabular-nums ${
                win ? 'text-emerald-300' : 'text-rose-300'
              }`}
            >
              {formatPct(prob, 0)}
            </span>
          </div>
        ))}
        {rows.length === 0 && (
          <p className="px-2 py-1 text-[11px] text-slate-500">None</p>
        )}
      </div>
    </div>
  )
}
