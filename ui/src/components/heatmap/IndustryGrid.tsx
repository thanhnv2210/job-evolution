import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { IndustrySummary } from '@/types/api'

type Props = {
  data: IndustrySummary[]
  selectedIndustry: string | null
  onSelect: (industry: string) => void
}

function scoreToFill(score: number | null, selected: boolean): string {
  const a = selected ? '1' : '0.72'
  if (score === null) return `rgba(100, 116, 139, ${selected ? '0.55' : '0.3'})`
  if (score < 35) return `rgba(52, 211, 153, ${a})`   // emerald — low risk
  if (score < 65) return `rgba(251, 191, 36, ${a})`   // amber — moderate
  return `rgba(248, 113, 113, ${a})`                   // red — high risk
}

type TooltipPayload = { payload: IndustrySummary }

function GlassTooltip({
  active,
  payload,
}: {
  active?: boolean
  payload?: TooltipPayload[]
}) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="rounded-xl border border-white/20 bg-slate-900/85 p-3 shadow-2xl backdrop-blur-lg text-sm">
      <p className="font-semibold text-white mb-1">{d.industry}</p>
      <p className="text-slate-300">{d.jobCount} jobs</p>
      <p className="text-slate-300">
        Avg score:{' '}
        <span className="font-medium text-white">
          {d.avgScore !== null ? d.avgScore.toFixed(1) : 'Not scored yet'}
        </span>
      </p>
      {d.scoredCount > 0 && (
        <p className="mt-1 text-xs text-slate-500">
          {d.scoredCount} / {d.jobCount} jobs scored
        </p>
      )}
    </div>
  )
}

export function IndustryGrid({ data, selectedIndustry, onSelect }: Props) {
  function handleClick(e: unknown) {
    const event = e as { activePayload?: TooltipPayload[] }
    const industry = event?.activePayload?.[0]?.payload?.industry
    if (industry) onSelect(industry)
  }

  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-md">
      <h2 className="text-lg font-semibold text-white/90">Industry Exposure Heatmap</h2>
      <p className="mt-0.5 text-sm text-slate-400 mb-6">
        Bar height = job count · Color = AI automatability risk · Click a bar to filter
      </p>

      {/* Accessible labels — also serve as test anchors */}
      <ul className="sr-only" aria-label="Industry list">
        {data.map(d => (
          <li key={d.industry} data-testid={`industry-label-${d.industry}`}>
            {d.industry}: {d.jobCount} jobs
            {d.avgScore !== null ? `, avg score ${d.avgScore.toFixed(1)}` : ''}
          </li>
        ))}
      </ul>

      <ResponsiveContainer width="100%" height={320}>
        <BarChart
          data={data}
          onClick={handleClick}
          margin={{ top: 8, right: 16, left: 0, bottom: 48 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="rgba(255,255,255,0.06)"
            vertical={false}
          />
          <XAxis
            dataKey="industry"
            tick={{ fill: 'rgba(255,255,255,0.55)', fontSize: 12 }}
            tickLine={false}
            axisLine={false}
            angle={-30}
            textAnchor="end"
            interval={0}
          />
          <YAxis
            tick={{ fill: 'rgba(255,255,255,0.35)', fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            label={{
              value: 'Jobs',
              angle: -90,
              position: 'insideLeft',
              fill: 'rgba(255,255,255,0.25)',
              fontSize: 11,
            }}
          />
          <Tooltip
            content={<GlassTooltip />}
            cursor={{ fill: 'rgba(255,255,255,0.03)' }}
          />
          <Bar dataKey="jobCount" radius={[4, 4, 0, 0]} isAnimationActive={false}>
            {data.map(entry => (
              <Cell
                key={entry.industry}
                fill={scoreToFill(entry.avgScore, entry.industry === selectedIndustry)}
                stroke={
                  entry.industry === selectedIndustry
                    ? 'rgba(255,255,255,0.45)'
                    : 'transparent'
                }
                strokeWidth={1.5}
                style={{ cursor: 'pointer' }}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="mt-3 flex flex-wrap justify-center gap-5">
        {[
          { fill: 'rgba(52, 211, 153, 0.72)', label: 'Low risk  < 35' },
          { fill: 'rgba(251, 191, 36, 0.72)', label: 'Moderate  35–65' },
          { fill: 'rgba(248, 113, 113, 0.72)', label: 'High risk  > 65' },
          { fill: 'rgba(100, 116, 139, 0.35)', label: 'Not scored' },
        ].map(({ fill, label }) => (
          <span key={label} className="flex items-center gap-1.5 text-xs text-slate-400">
            <span
              aria-hidden="true"
              className="inline-block h-2.5 w-2.5 rounded-sm"
              style={{ backgroundColor: fill }}
            />
            {label}
          </span>
        ))}
      </div>
    </div>
  )
}
