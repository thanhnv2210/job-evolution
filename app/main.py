import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from dotenv import load_dotenv

from .models import Job, JobScoreResponse
from .scorer import score_job

load_dotenv()

DATA_FILE = Path(__file__).parent.parent / "data" / "fintech_green_jobs_100.json"

# In-memory store: populated at startup, scores cached on demand
_jobs: dict[int, Job] = {}
_scores: dict[int, JobScoreResponse] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    raw = json.loads(DATA_FILE.read_text())
    for item in raw:
        job = Job(**item)
        _jobs[job.id] = job
    print(f"Loaded {len(_jobs)} jobs from {DATA_FILE.name}")
    yield
    _jobs.clear()
    _scores.clear()


app = FastAPI(
    title="Job Evolution — AI Automatability Scorer",
    description=(
        "Reads fintech & green jobs data and uses Claude to score "
        "how automatable each daily task is."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ── Job listing ─────────────────────────────────────────────────────────────

@app.get("/jobs", response_model=list[Job], summary="List all jobs")
def list_jobs():
    return list(_jobs.values())


@app.get("/jobs/{job_id}", response_model=Job, summary="Get a single job")
def get_job(job_id: int):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


# ── Scoring ──────────────────────────────────────────────────────────────────

@app.post(
    "/jobs/{job_id}/score",
    response_model=JobScoreResponse,
    summary="Score a job's tasks for AI automatability",
    description=(
        "Calls Claude to evaluate each daily task and returns a 0-100 "
        "AI automatability score with reasoning. Results are cached in memory."
    ),
)
async def score_job_endpoint(job_id: int, force: bool = False):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if not force and job_id in _scores:
        return _scores[job_id]

    result = await score_job(job)
    _scores[job_id] = result
    return result


@app.get(
    "/jobs/{job_id}/score",
    response_model=JobScoreResponse,
    summary="Get cached score for a job (404 if not yet scored)",
)
def get_score(job_id: int):
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    if job_id not in _scores:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} has not been scored yet. POST /jobs/{job_id}/score first.",
        )
    return _scores[job_id]


async def _score_all_background():
    for job_id, job in _jobs.items():
        if job_id not in _scores:
            _scores[job_id] = await score_job(job)


@app.post(
    "/jobs/score-all",
    summary="Score all jobs in the background",
    description=(
        "Kicks off background scoring for every job not yet scored. "
        "Already-scored jobs are skipped unless you clear the cache. "
        "Poll GET /jobs/{id}/score to retrieve results as they complete."
    ),
)
async def score_all(background_tasks: BackgroundTasks):
    pending = [jid for jid in _jobs if jid not in _scores]
    background_tasks.add_task(_score_all_background)
    return {
        "message": f"Scoring {len(pending)} jobs in the background.",
        "pending_job_ids": pending,
    }


@app.delete(
    "/scores",
    summary="Clear all cached scores",
)
def clear_scores():
    count = len(_scores)
    _scores.clear()
    return {"cleared": count}
