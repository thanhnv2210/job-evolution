# Job Evolution Tracker

Analyze how vulnerable job roles are to AI automation. Powered by Claude Opus 4.6, this tool scores each task in a job's daily workload on a 0–100 automatability scale and surfaces the results in an interactive dashboard.

![Dashboard](https://img.shields.io/badge/stack-FastAPI%20%2B%20React-blue)
![Python](https://img.shields.io/badge/python-3.12-blue)
![TypeScript](https://img.shields.io/badge/typescript-5.9-blue)

---

## Features

- **Per-task AI scoring** — Claude Opus 4.6 evaluates each daily task individually with reasoning
- **Industry heatmap** — bar chart aggregating average automatability risk by industry
- **Job list panel** — expandable cards with task-by-task score breakdowns and color-coded risk badges
- **Score persistence** — PostgreSQL stores score history; re-scoring a job appends a new record
- **Concurrent batch scoring** — `POST /score-all` runs all jobs in parallel with a configurable semaphore
- **Ollama fallback** — automatically falls back to a local Ollama model when Anthropic credits are exhausted

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI 0.115, Uvicorn, Pydantic v2 |
| AI | Anthropic Claude Opus 4.6 / Ollama (fallback) |
| Database | PostgreSQL + SQLAlchemy 2 async + Alembic |
| Frontend | React 19, TypeScript 5.9, Vite |
| UI | Tailwind CSS v4, shadcn/ui, Recharts, Lucide |

---

## Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 15+ (or Docker — see below)
- An [Anthropic API key](https://console.anthropic.com/)
- _(Optional)_ [Ollama](https://ollama.com) for local fallback

---

## Quick Start

### 1. Clone & configure

```bash
git clone <repo-url>
cd job-evolution
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY
```

### 2. Start PostgreSQL

**Option A — Docker (recommended):**
```bash
docker-compose up -d
```

**Option B — local Postgres:**
```bash
createdb job_evolution
# Update DATABASE_URL in .env if needed
```

### 3. Backend setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head             # Run DB migrations
uvicorn app.main:app --reload
```

API available at `http://localhost:8000` — docs at `http://localhost:8000/docs`.

### 4. Frontend setup

```bash
cd ui
npm install
npm run dev
```

Dashboard available at `http://localhost:5173`.

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Yes | — | API key for Claude Opus 4.6 scoring |
| `DATABASE_URL` | Yes | — | PostgreSQL async connection string |
| `OLLAMA_BASE_URL` | No | `http://localhost:11434` | Ollama server URL (fallback scorer) |
| `OLLAMA_MODEL` | No | `mistral` | Ollama model name |
| `SCORER_CONCURRENCY` | No | `5` | Max concurrent LLM calls during `score-all` |

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/jobs` | List all 100 jobs |
| `GET` | `/jobs/{id}` | Get a single job |
| `POST` | `/jobs/{id}/score` | Score a job (cached in DB) |
| `GET` | `/jobs/{id}/score` | Retrieve cached score |
| `GET` | `/jobs/{id}/score/history` | Full score history for a job |
| `POST` | `/score-all` | Batch-score all jobs concurrently |
| `DELETE` | `/scores` | Clear in-memory score cache |

Interactive docs: `http://localhost:8000/docs`

---

## Scoring Rubric

Each daily task is scored 0–100:

| Range | Risk Level | Meaning |
|-------|-----------|---------|
| 0–34 | Low | Requires human judgment, creativity, or physical presence |
| 35–65 | Moderate | Partially automatable; augmentation likely |
| 66–100 | High | Highly automatable with current or near-term AI |

The job's overall score is the mean of all task scores.

---

## Project Structure

```
job-evolution/
├── app/
│   ├── main.py            # FastAPI app and API routes
│   ├── scorer.py          # Claude Opus 4.6 scoring logic
│   ├── ollama_scorer.py   # Ollama fallback scorer
│   ├── models.py          # Pydantic request/response models
│   ├── database.py        # Async SQLAlchemy setup
│   ├── db_models.py       # ORM models (ScoreRecord)
│   └── logging_config.py  # Logging configuration
├── ui/
│   └── src/
│       ├── components/
│       │   ├── heatmap/   # IndustryGrid bar chart
│       │   └── jobs/      # JobListPanel with expandable cards
│       ├── hooks/         # useJobs, useAllScores, useJobScore
│       ├── context/       # SelectionContext (selected industry/job)
│       └── types/api.ts   # TypeScript types mirroring backend models
├── alembic/               # Database migrations
├── data/
│   └── fintech_green_jobs_100.json   # 100 FinTech/Green job records
├── docker-compose.yml     # PostgreSQL + pgAdmin
├── .env.example           # Environment variable template
└── requirements.txt       # Python dependencies
```

---

## Development

### Run backend tests
```bash
cd app
pytest
```

### Run frontend tests
```bash
cd ui
npm test
```

### Add a shadcn/ui component
```bash
cd ui
npx shadcn@latest add <component-name>
```
> Never manually edit files inside `ui/src/components/ui/` — they are auto-generated.

### Create a new DB migration
```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

---

## Using the Ollama Fallback

Install [Ollama](https://ollama.com), pull a model, and set the variables in `.env`:

```bash
ollama pull mistral
```

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
```

The fallback activates automatically when the Anthropic scorer detects credit exhaustion. You can also raise `SCORER_CONCURRENCY` significantly when using Ollama since there are no external rate limits.

---

## License

MIT
