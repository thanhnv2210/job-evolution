import { useCallback, useState } from 'react'
import type { JobScoreResponse } from '@/types/api'

const API_BASE = 'http://localhost:8000'

/**
 * Fetches and triggers scoring for a single job on demand.
 * Used when expanding a job card that hasn't been scored yet.
 */
export function useJobScore() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchScore = useCallback(
    async (jobId: number): Promise<JobScoreResponse | null> => {
      setLoading(true)
      setError(null)
      try {
        // Try cached score first
        const cached = await fetch(`${API_BASE}/jobs/${jobId}/score`)
        if (cached.ok) return (await cached.json()) as JobScoreResponse

        // Not scored yet — trigger scoring
        const scored = await fetch(`${API_BASE}/jobs/${jobId}/score`, { method: 'POST' })
        if (!scored.ok) throw new Error(`HTTP ${scored.status}`)
        return (await scored.json()) as JobScoreResponse
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to score job')
        return null
      } finally {
        setLoading(false)
      }
    },
    [],
  )

  return { fetchScore, loading, error }
}
