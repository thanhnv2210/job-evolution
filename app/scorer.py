import json
import anthropic
from .models import Job, TaskScore, JobScoreResponse

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


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic()
    return _client


async def score_job(job: Job) -> JobScoreResponse:
    """Score each daily task of a job for AI automatability using Claude."""
    client = get_client()

    task_list = "\n".join(f"- {task}" for task in job.daily_tasks)
    user_prompt = f"""\
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

    # Use streaming to avoid HTTP timeouts on longer responses
    task_scores: list[TaskScore] = []

    async with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        final = await stream.get_final_message()

    # Extract JSON from the text response
    raw_text = next(
        block.text for block in final.content if block.type == "text"
    )
    data = json.loads(raw_text)

    for item in data["task_scores"]:
        task_scores.append(TaskScore(**item))

    overall = round(sum(ts.score for ts in task_scores) / len(task_scores), 1)

    return JobScoreResponse(
        job_id=job.id,
        role=job.role,
        industry=job.industry,
        seniority=job.seniority,
        task_scores=task_scores,
        overall_score=overall,
    )
