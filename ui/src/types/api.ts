export type Job = {
  id: number
  role: string
  industry: string
  seniority: string
  summary: string
  skills: string[]
  tech_stack: string[]
  salary_range_usd: string
  daily_tasks: string[]
}

export type TaskScore = {
  task: string
  score: number
  reasoning: string
}

export type JobScoreResponse = {
  job_id: number
  role: string
  industry: string
  seniority: string
  task_scores: TaskScore[]
  overall_score: number
  model_used: string | null
  scored_at: string | null
}

export type IndustrySummary = {
  industry: string
  jobCount: number
  scoredCount: number
  avgScore: number | null
}
