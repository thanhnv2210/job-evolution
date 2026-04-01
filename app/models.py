from pydantic import BaseModel, Field


class Job(BaseModel):
    id: int
    role: str
    industry: str
    seniority: str
    summary: str
    skills: list[str]
    tech_stack: list[str]
    salary_range_usd: str
    daily_tasks: list[str]


class TaskScore(BaseModel):
    task: str = Field(description="The daily task being scored")
    score: int = Field(
        ge=0,
        le=100,
        description=(
            "AI automatability score from 0 (fully human) to 100 (fully automatable). "
            "0-20: requires deep human judgment, creativity, or physical presence. "
            "21-40: AI can assist but human drives. "
            "41-60: roughly equal human/AI contribution. "
            "61-80: AI leads but human oversight needed. "
            "81-100: AI can do this end-to-end with minimal human input."
        ),
    )
    reasoning: str = Field(description="Brief explanation of the score (1-2 sentences)")


class JobScoreResponse(BaseModel):
    job_id: int
    role: str
    industry: str
    seniority: str
    task_scores: list[TaskScore]
    overall_score: float = Field(description="Mean automatability score across all tasks")
