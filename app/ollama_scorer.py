"""
Fallback scorer using a locally-running Ollama instance.

Ollama exposes an OpenAI-compatible endpoint at /v1/chat/completions so we
call it directly with httpx — no extra dependency required.

Setup (one-time):
    brew install ollama          # or: https://ollama.com
    ollama serve                 # starts the daemon on :11434
    ollama pull llama3.2         # ~2 GB — or any model you prefer

Environment variables (optional, sensible defaults provided):
    OLLAMA_BASE_URL   default: http://localhost:11434
    OLLAMA_MODEL      default: llama3.2
"""
import json
import logging
import os
import re

import httpx

from .models import Job, TaskScore, JobScoreResponse
from .scorer import SYSTEM_PROMPT, build_user_prompt, build_response

log = logging.getLogger(__name__)

_OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
_TIMEOUT = httpx.Timeout(connect=10.0, read=300.0, write=30.0, pool=10.0)


def _strip_fences(text: str) -> str:
    """Remove ```json … ``` or ``` … ``` that local models often add."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if match:
        return match.group(1)
    return text


async def score_job_ollama(job: Job) -> JobScoreResponse:
    """Score a job's tasks using the local Ollama model."""
    url = f"{_OLLAMA_BASE_URL}/v1/chat/completions"
    payload = {
        "model": _OLLAMA_MODEL,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(job)},
        ],
    }

    log.info(
        "Ollama fallback: scoring job %d (%s) with model=%s",
        job.id, job.role, _OLLAMA_MODEL,
    )

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        try:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
        except httpx.ConnectError:
            raise RuntimeError(
                f"Ollama is not running at {_OLLAMA_BASE_URL}. "
                "Start it with: ollama serve"
            )
        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"Ollama request failed ({e.response.status_code}): {e.response.text}"
            )

    raw_text = resp.json()["choices"][0]["message"]["content"]
    log.debug("Ollama raw response for job %d: %s", job.id, raw_text[:200])

    try:
        data = json.loads(_strip_fences(raw_text))
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Ollama returned non-JSON for job {job.id}: {raw_text[:300]}"
        ) from exc

    return build_response(job, data)
