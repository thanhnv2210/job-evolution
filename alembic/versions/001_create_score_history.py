"""create score_history table

Revision ID: 001
Revises:
Create Date: 2026-04-01
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "score_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("industry", sa.String(), nullable=False),
        sa.Column("seniority", sa.String(), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("task_scores", sa.JSON(), nullable=False),
        sa.Column("model_used", sa.String(), nullable=False),
        sa.Column("scored_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_score_history_job_id", "score_history", ["job_id"])


def downgrade() -> None:
    op.drop_index("ix_score_history_job_id", table_name="score_history")
    op.drop_table("score_history")
