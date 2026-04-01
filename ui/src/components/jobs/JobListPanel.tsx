import { useState } from 'react'
import { AlertTriangle, Bot, ChevronDown, ChevronUp, Loader2, Zap } from 'lucide-react'
import type { Job, JobScoreResponse, TaskScore } from '@/types/api'
import { useJobScore } from '@/hooks/useJobScore'

type Props = {
  industry: string
  jobs: Job[]
  scoreMap: Map<number, JobScoreResponse>
  selectedJobId: number | null
  onSelectJob: (id: number | null) => void
  onScoreLoaded: (score: JobScoreResponse) => void
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function riskLabel(score: number | null): { label: string; color: string; bg: string; border: string } {
  if (score === null) return { label: 'Not scored', color: 'text-slate-400', bg: 'bg-slate-400/10', border: 'border-slate-500/20' }
  if (score < 35)     return { label: 'Low risk',    color: 'text-emerald-400', bg: 'bg-emerald-400/10', border: 'border-emerald-500/25' }
  if (score < 65)     return { label: 'Moderate',    color: 'text-amber-400',   bg: 'bg-amber-400/10',   border: 'border-amber-500/25' }
  return               { label: 'High risk',   color: 'text-red-400',     bg: 'bg-red-400/10',     border: 'border-red-500/25' }
}

function taskBarColor(score: number): string {
  if (score < 35) return 'bg-emerald-400'
  if (score < 65) return 'bg-amber-400'
  return 'bg-red-400'
}

function formatDate(iso: string | null): string {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

// ── TaskRow ───────────────────────────────────────────────────────────────────

function TaskRow({ task }: { task: TaskScore }) {
  const color = taskBarColor(task.score)
  return (
    <li className="space-y-1">
      <div className="flex items-center justify-between gap-3">
        <span className="text-xs text-slate-300 leading-snug flex-1">{task.task}</span>
        <span className={`text-xs font-bold tabular-nums shrink-0 ${
          task.score < 35 ? 'text-emerald-400' : task.score < 65 ? 'text-amber-400' : 'text-red-400'
        }`}>
          {task.score}
        </span>
      </div>
      <div className="h-1 w-full rounded-full bg-white/10">
        <div
          className={`h-1 rounded-full transition-all ${color}`}
          style={{ width: `${task.score}%` }}
        />
      </div>
      <p className="text-xs text-slate-500 leading-snug">{task.reasoning}</p>
    </li>
  )
}

// ── JobCard ───────────────────────────────────────────────────────────────────

function JobCard({
  job,
  score,
  isExpanded,
  onToggle,
  onScoreLoaded,
}: {
  job: Job
  score: JobScoreResponse | undefined
  isExpanded: boolean
  onToggle: () => void
  onScoreLoaded: (s: JobScoreResponse) => void
}) {
  const { fetchScore, loading } = useJobScore()
  const [localScore, setLocalScore] = useState<JobScoreResponse | undefined>(score)
  const risk = riskLabel(localScore?.overall_score ?? null)

  async function handleToggle() {
    if (!isExpanded && !localScore) {
      const fetched = await fetchScore(job.id)
      if (fetched) {
        setLocalScore(fetched)
        onScoreLoaded(fetched)
      }
    }
    onToggle()
  }

  const overallScore = localScore?.overall_score ?? null

  return (
    <div
      className={`rounded-xl border transition-colors ${
        isExpanded ? 'border-white/20 bg-white/8' : 'border-white/8 bg-white/4 hover:border-white/15 hover:bg-white/6'
      } backdrop-blur-sm`}
    >
      {/* Header row */}
      <button
        onClick={() => void handleToggle()}
        className="flex w-full items-center gap-3 p-4 text-left"
      >
        {/* Risk color strip */}
        <span
          className={`h-10 w-1 shrink-0 rounded-full ${
            overallScore === null ? 'bg-slate-600'
            : overallScore < 35 ? 'bg-emerald-400'
            : overallScore < 65 ? 'bg-amber-400'
            : 'bg-red-400'
          }`}
        />

        <div className="flex-1 min-w-0">
          <p className="font-medium text-white truncate">{job.role}</p>
          <p className="text-xs text-slate-400">{job.seniority}</p>
        </div>

        {/* Score badge */}
        {overallScore !== null ? (
          <span className={`shrink-0 rounded-lg border px-2.5 py-1 text-sm font-bold tabular-nums ${risk.color} ${risk.bg} ${risk.border}`}>
            {overallScore.toFixed(1)}
          </span>
        ) : (
          <span className="shrink-0 rounded-lg border border-slate-500/20 bg-slate-400/10 px-2.5 py-1 text-xs text-slate-500">
            —
          </span>
        )}

        {loading ? (
          <Loader2 className="h-4 w-4 shrink-0 animate-spin text-slate-400" />
        ) : isExpanded ? (
          <ChevronUp className="h-4 w-4 shrink-0 text-slate-400" />
        ) : (
          <ChevronDown className="h-4 w-4 shrink-0 text-slate-400" />
        )}
      </button>

      {/* Expanded detail */}
      {isExpanded && (
        <div className="border-t border-white/8 px-4 pb-4 pt-3 space-y-4">
          {/* Meta row */}
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
            {localScore?.model_used && (
              <span className="flex items-center gap-1">
                <Bot className="h-3 w-3" />
                {localScore.model_used}
              </span>
            )}
            {localScore?.scored_at && (
              <span>Scored {formatDate(localScore.scored_at)}</span>
            )}
            {overallScore !== null && (
              <span className={`flex items-center gap-1 font-medium ${risk.color}`}>
                <AlertTriangle className="h-3 w-3" />
                {risk.label}
              </span>
            )}
          </div>

          {/* Task scores */}
          {localScore ? (
            <ul className="space-y-3">
              {[...localScore.task_scores]
                .sort((a, b) => b.score - a.score)
                .map(task => (
                  <TaskRow key={task.task} task={task} />
                ))}
            </ul>
          ) : (
            <p className="text-xs text-slate-500 italic">
              No score available — expand triggers scoring automatically.
            </p>
          )}

          {/* Skills + tech */}
          <div className="flex flex-wrap gap-1.5 pt-1">
            {job.skills.slice(0, 5).map(s => (
              <span key={s} className="rounded-md border border-white/10 bg-white/5 px-2 py-0.5 text-xs text-slate-400">
                {s}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ── JobListPanel ──────────────────────────────────────────────────────────────

export function JobListPanel({ industry, jobs, scoreMap, selectedJobId, onSelectJob, onScoreLoaded }: Props) {
  const sortedJobs = [...jobs].sort((a, b) => {
    const sa = scoreMap.get(a.id)?.overall_score ?? -1
    const sb = scoreMap.get(b.id)?.overall_score ?? -1
    return sb - sa
  })

  const scoredCount = jobs.filter(j => scoreMap.has(j.id)).length

  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-md space-y-4">
      {/* Panel header */}
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-white/90 flex items-center gap-2">
            <Zap className="h-4 w-4 text-amber-400" />
            {industry}
          </h2>
          <p className="text-sm text-slate-400 mt-0.5">
            {jobs.length} jobs · {scoredCount} scored · sorted by highest AI exposure
          </p>
        </div>
        <span className="text-xs text-slate-500 bg-white/5 border border-white/10 rounded-lg px-2.5 py-1">
          Click a job to expand tasks
        </span>
      </div>

      {/* Job cards */}
      <div className="space-y-2">
        {sortedJobs.map(job => (
          <JobCard
            key={job.id}
            job={job}
            score={scoreMap.get(job.id)}
            isExpanded={selectedJobId === job.id}
            onToggle={() => onSelectJob(selectedJobId === job.id ? null : job.id)}
            onScoreLoaded={onScoreLoaded}
          />
        ))}
      </div>
    </div>
  )
}
