import { useMemo } from 'react'
import { AlertCircle, Loader2, RefreshCw } from 'lucide-react'
import { IndustryGrid } from './IndustryGrid'
import { useJobs } from '@/hooks/useJobs'
import { useAllScores } from '@/hooks/useAllScores'
import { useSelection } from '@/context/SelectionContext'
import type { IndustrySummary } from '@/types/api'

export function HeatmapView() {
  const { jobs, loading: jobsLoading, error: jobsError } = useJobs()

  const jobIds = useMemo(() => jobs.map(j => j.id), [jobs])
  const { scores, loading: scoresLoading, refetch } = useAllScores(jobIds)

  const { selectedIndustry, setSelectedIndustry } = useSelection()

  const industryData = useMemo((): IndustrySummary[] => {
    const scoreMap = new Map(scores.map(s => [s.job_id, s.overall_score]))

    const byIndustry = new Map<string, { jobCount: number; scoreValues: number[] }>()
    for (const job of jobs) {
      const entry = byIndustry.get(job.industry) ?? { jobCount: 0, scoreValues: [] }
      entry.jobCount++
      const s = scoreMap.get(job.id)
      if (s !== undefined) entry.scoreValues.push(s)
      byIndustry.set(job.industry, entry)
    }

    return Array.from(byIndustry.entries())
      .map(([industry, { jobCount, scoreValues }]) => ({
        industry,
        jobCount,
        scoredCount: scoreValues.length,
        avgScore:
          scoreValues.length > 0
            ? scoreValues.reduce((a, b) => a + b, 0) / scoreValues.length
            : null,
      }))
      .sort((a, b) => (b.avgScore ?? -1) - (a.avgScore ?? -1))
  }, [jobs, scores])

  if (jobsLoading) {
    return (
      <div className="flex items-center justify-center gap-2 py-24 text-slate-400">
        <Loader2 className="h-5 w-5 animate-spin" />
        <span>Loading jobs…</span>
      </div>
    )
  }

  if (jobsError) {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
        <AlertCircle className="h-4 w-4 shrink-0" />
        Failed to load jobs: {jobsError}. Is the backend running on port 8000?
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-400">
          {scores.length > 0
            ? `${scores.length} of ${jobs.length} jobs scored`
            : 'No scores loaded — click Refresh to pull cached scores from the backend'}
        </p>
        <button
          onClick={() => void refetch()}
          disabled={scoresLoading || jobIds.length === 0}
          className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-300 backdrop-blur-sm transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${scoresLoading ? 'animate-spin' : ''}`} />
          {scoresLoading ? 'Loading…' : 'Refresh scores'}
        </button>
      </div>

      <IndustryGrid
        data={industryData}
        selectedIndustry={selectedIndustry}
        onSelect={setSelectedIndustry}
      />

      {selectedIndustry && (
        <p className="text-center text-sm text-slate-400">
          Filtering by{' '}
          <span className="font-medium text-white">{selectedIndustry}</span>
          {' · '}
          <button
            onClick={() => setSelectedIndustry(null)}
            className="underline decoration-dotted hover:text-slate-200"
          >
            clear
          </button>
        </p>
      )}
    </div>
  )
}
