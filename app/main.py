import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# load_dotenv() must run before any local imports that read env vars at
# module level (database.py reads DATABASE_URL when the module is imported)
load_dotenv()

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from .database import AsyncSessionLocal, engine, get_db  # noqa: E402
from .db_models import ScoreRecord  # noqa: E402
from .logging_config import configure_logging  # noqa: E402
from .models import Job, JobScoreResponse  # noqa: E402
from .scorer import score_job  # noqa: E402

configure_logging()

log = logging.getLogger(__name__)

DATA_FILE = Path(__file__).parent.parent / "data" / "fintech_green_jobs_100.json"

# In-memory store: populated at startup, scores cached on demand
_jobs: dict[int, Job] = {}
_scores: dict[int, JobScoreResponse] = {}


def _record_to_response(record: ScoreRecord) -> JobScoreResponse:
    return JobScoreResponse(
        job_id=record.job_id,
        role=record.role,
        industry=record.industry,
        seniority=record.seniority,
        task_scores=record.task_scores,
        overall_score=record.overall_score,
        model_used=record.model_used,
        scored_at=record.scored_at,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables (idempotent)
    from .db_models import ScoreRecord as _  # noqa: F401 — ensure ORM metadata loaded
    async with engine.begin() as conn:
        from .database import Base
        await conn.run_sync(Base.metadata.create_all)
    log.info("Database tables ensured")

    # Load jobs from JSON
    raw = json.loads(DATA_FILE.read_text())
    for item in raw:
        job = Job(**item)
        _jobs[job.id] = job
    log.info("Loaded %d jobs from %s", len(_jobs), DATA_FILE.name)

    # Pre-populate in-memory cache with latest scored result per job
    async with AsyncSessionLocal() as session:
        for job_id in _jobs:
            result = await session.execute(
                select(ScoreRecord)
                .where(ScoreRecord.job_id == job_id)
                .order_by(ScoreRecord.scored_at.desc())
                .limit(1)
            )
            record = result.scalar_one_or_none()
            if record:
                _scores[job_id] = _record_to_response(record)

    log.info("Pre-loaded %d cached scores from database", len(_scores))
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)


# ── Job listing ──────────────────────────────────────────────────────────────

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
        "AI automatability score with reasoning. Results are persisted to "
        "the database and cached in memory."
    ),
)
async def score_job_endpoint(
    job_id: int,
    force: bool = False,
    db: AsyncSession = Depends(get_db),
):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if not force and job_id in _scores:
        log.debug("Cache hit for job %d", job_id)
        return _scores[job_id]

    log.info("Scoring job %d (%s, %s)", job_id, job.role, job.seniority)
    try:
        result = await score_job(job)
    except Exception:
        log.exception("Failed to score job %d", job_id)
        raise HTTPException(status_code=500, detail="LLM scoring failed — check logs for details")

    # Persist to DB
    now = datetime.now(timezone.utc)
    record = ScoreRecord(
        job_id=result.job_id,
        role=result.role,
        industry=result.industry,
        seniority=result.seniority,
        overall_score=result.overall_score,
        task_scores=[ts.model_dump() for ts in result.task_scores],
        model_used=result.model_used or "unknown",
        scored_at=now,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    result = result.model_copy(update={"scored_at": record.scored_at})
    _scores[job_id] = result
    log.info("Job %d scored — overall %.1f (model=%s)", job_id, result.overall_score, result.model_used)
    return result


@app.get(
    "/jobs/{job_id}/score",
    response_model=JobScoreResponse,
    summary="Get cached score for a job (404 if not yet scored)",
)
async def get_score(job_id: int, db: AsyncSession = Depends(get_db)):
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job_id in _scores:
        return _scores[job_id]

    # Fallback: check DB directly (e.g. after a restart race)
    result = await db.execute(
        select(ScoreRecord)
        .where(ScoreRecord.job_id == job_id)
        .order_by(ScoreRecord.scored_at.desc())
        .limit(1)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} has not been scored yet. POST /jobs/{job_id}/score first.",
        )
    response = _record_to_response(record)
    _scores[job_id] = response
    return response


@app.get(
    "/jobs/{job_id}/score/history",
    response_model=list[JobScoreResponse],
    summary="Get all historical scores for a job (newest first)",
)
async def get_score_history(job_id: int, db: AsyncSession = Depends(get_db)):
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    result = await db.execute(
        select(ScoreRecord)
        .where(ScoreRecord.job_id == job_id)
        .order_by(ScoreRecord.scored_at.desc())
    )
    records = result.scalars().all()
    return [_record_to_response(r) for r in records]


async def _score_all_background():
    async with AsyncSessionLocal() as db:
        for job_id, job in _jobs.items():
            if job_id not in _scores:
                log.info("Background scoring job %d (%s)", job_id, job.role)
                try:
                    result = await score_job(job)
                    now = datetime.now(timezone.utc)
                    record = ScoreRecord(
                        job_id=result.job_id,
                        role=result.role,
                        industry=result.industry,
                        seniority=result.seniority,
                        overall_score=result.overall_score,
                        task_scores=[ts.model_dump() for ts in result.task_scores],
                        model_used=result.model_used or "unknown",
                        scored_at=now,
                    )
                    db.add(record)
                    await db.commit()
                    await db.refresh(record)
                    _scores[job_id] = result.model_copy(update={"scored_at": record.scored_at})
                except Exception:
                    log.exception("Background scoring failed for job %d", job_id)


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
    log.info("Queuing background scoring for %d jobs", len(pending))
    background_tasks.add_task(_score_all_background)
    return {
        "message": f"Scoring {len(pending)} jobs in the background.",
        "pending_job_ids": pending,
    }


@app.delete("/scores", summary="Clear all cached scores")
def clear_scores():
    count = len(_scores)
    _scores.clear()
    log.info("Cleared %d cached scores", count)
    return {"cleared": count}
