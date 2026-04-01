import json
import logging

import anthropic
import httpx
from .models import Job, TaskScore, JobScoreResponse

log = logging.getLogger(__name__)

# connect=30 s  — generous for first TLS handshake (default is 5 s, which was too tight)
# read=600 s    — streaming LLM with adaptive thinking can easily take minutes
# write=30 s    — sending the prompt
# pool=30 s     — waiting for a free connection from the pool
_TIMEOUT = httpx.Timeout(connect=30.0, read=600.0, write=30.0, pool=30.0)

_client: anthropic.AsyncAnthropic | None = None

SYSTEM_PROMPT = """\
You are an expert in the future of work and AI automation. Your task is to score \
the 'AI Automatability' of job tasks on a 0-100 scale.

Scoring rubric:
- 0-20: Requires deep human judgment, creativity, empathy, or physical presence. \
AI cannot meaningfully assist.
- 21-40: AI can assist with research or drafting, but a human must drive the work.
- 41-60: Roughly equal human/AI contribution; AI handles routine parts, human handles edge cases.
- 61-80: AI can lead this task with human oversight and review.
- 81-100: AI can execute end-to-end with minimal human input.

Consider factors like: structured vs. unstructured data, repetitiveness, required context, \
regulatory constraints, creative demands, and interpersonal complexity.\
"""


def build_user_prompt(job: Job) -> str:
    task_list = "\n".join(f"- {task}" for task in job.daily_tasks)
    return f"""\
Score the AI automatability of each daily task for the following role:

Role: {job.role}
Industry: {job.industry}
Seniority: {job.seniority}
Skills used: {", ".join(job.skills)}
Tech stack: {", ".join(job.tech_stack)}

Daily tasks to score:
{task_list}

Return a JSON object with a "task_scores" array. Each element must have:
- "task": the exact task string from above
- "score": integer 0-100
- "reasoning": 1-2 sentence explanation

Return ONLY valid JSON, no markdown fences.\
"""


def build_response(job: Job, data: dict, model_used: str) -> JobScoreResponse:
    task_scores = [TaskScore(**item) for item in data["task_scores"]]
    overall = round(sum(ts.score for ts in task_scores) / len(task_scores), 1)
    return JobScoreResponse(
        job_id=job.id,
        role=job.role,
        industry=job.industry,
        seniority=job.seniority,
        task_scores=task_scores,
        overall_score=overall,
        model_used=model_used,
    )


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(timeout=_TIMEOUT)
        log.debug(
            "Anthropic client created (connect=%.0fs read=%.0fs)",
            _TIMEOUT.connect,
            _TIMEOUT.read,
        )
    return _client


def _is_credit_error(exc: anthropic.BadRequestError) -> bool:
    try:
        return "credit balance is too low" in exc.body["error"]["message"]
    except (TypeError, KeyError):
        return False


async def score_job(job: Job) -> JobScoreResponse:
    """Score each daily task for AI automatability.

    Primary path: Claude Opus 4.6 (Anthropic).
    Fallback: local Ollama model — activated automatically when Anthropic
    returns a 400 'credit balance too low' error.
    """
    client = get_client()

    log.debug("Calling Claude for job %d (%s)", job.id, job.role)
    try:
        async with client.messages.stream(
            model="claude-opus-4-6",
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_user_prompt(job)}],
        ) as stream:
            final = await stream.get_final_message()

        log.debug(
            "Claude responded for job %d — input_tokens=%s output_tokens=%s",
            job.id,
            final.usage.input_tokens,
            final.usage.output_tokens,
        )

        raw_text = next(
            block.text for block in final.content if block.type == "text"
        )
        return build_response(job, json.loads(raw_text), model_used="claude-opus-4-6")

    except anthropic.BadRequestError as exc:
        if not _is_credit_error(exc):
            raise
        log.warning(
            "Anthropic credit exhausted for job %d — switching to Ollama fallback",
            job.id,
        )

    # Import here to avoid a circular dependency at module load time
    from .ollama_scorer import score_job_ollama
    return await score_job_ollama(job)
