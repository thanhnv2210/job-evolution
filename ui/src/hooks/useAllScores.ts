import { useCallback, useState } from 'react'
import type { JobScoreResponse } from '@/types/api'

const API_BASE = 'http://localhost:8000'

/**
 * Fetches all cached scores from the backend in parallel.
 * Jobs that have not been scored yet silently return nothing (404s are ignored).
 * Does NOT auto-fetch on mount — call `refetch` explicitly (e.g. on a button click).
 *
 * @param jobIds - Stable array of job IDs (memoize at call site with useMemo).
 */
export function useAllScores(jobIds: readonly number[]) {
  const [scores, setScores] = useState<JobScoreResponse[]>([])
  const [loading, setLoading] = useState(false)

  const refetch = useCallback(async () => {
    if (jobIds.length === 0) return
    setLoading(true)
    try {
      const settled = await Promise.allSettled(
        jobIds.map(id =>
          fetch(`${API_BASE}/jobs/${id}/score`).then(r =>
            r.ok ? (r.json() as Promise<JobScoreResponse>) : Promise.reject()
          )
        )
      )
      setScores(
        settled
          .filter((r): r is PromiseFulfilledResult<JobScoreResponse> => r.status === 'fulfilled')
          .map(r => r.value)
      )
    } finally {
      setLoading(false)
    }
  }, [jobIds]) // eslint-disable-line react-hooks/exhaustive-deps

  return { scores, loading, refetch }
}
