import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { probColor } from '../utils/colors'

// Horizontal bar chart of the most likely champions (Recharts).
export default function ProbabilityChart({ teams = [], topN = 10 }) {
  const data = teams.slice(0, topN).map((t) => ({
    id: t.team_id,
    name: `${t.flag} ${t.name}`,
    prob: +(t.championship_probability * 100).toFixed(2),
  }))

  if (data.length === 0) return null

  return (
    <div className="rounded-2xl border border-slate-700/60 bg-slate-900/60 p-5 shadow-lg backdrop-blur">
      <h2 className="mb-4 text-sm font-bold uppercase tracking-wider text-slate-400">
        Championship odds — top {data.length}
      </h2>
      <ResponsiveContainer width="100%" height={Math.max(240, data.length * 34)}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 0, right: 48, bottom: 0, left: 8 }}
        >
          <XAxis
            type="number"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            tickFormatter={(v) => `${v}%`}
            domain={[0, 'dataMax']}
            axisLine={{ stroke: '#334155' }}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="name"
            width={140}
            tick={{ fill: '#e2e8f0', fontSize: 13 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            cursor={{ fill: 'rgba(148,163,184,0.08)' }}
            contentStyle={{
              background: '#0f172a',
              border: '1px solid #334155',
              borderRadius: 8,
              color: '#e2e8f0',
            }}
            formatter={(v) => [`${v}%`, 'Win probability']}
          />
          <Bar dataKey="prob" radius={[0, 6, 6, 0]} barSize={20} isAnimationActive>
            {data.map((d) => (
              <Cell key={d.id} fill={probColor(d.prob / 100)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
