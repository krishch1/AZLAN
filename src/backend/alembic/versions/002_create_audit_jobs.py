"""create audit_jobs table

Revision ID: 002_create_audit_jobs
Revises: 001_create_audit_domain_models
Create Date: 2025-01-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "002_create_audit_jobs"
down_revision = "001_create_audit_domain_models"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("audit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("worker_id", sa.String(length=128), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, default=0),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["audit_id"], ["audits.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_audit_jobs_audit_id"), "audit_jobs", ["audit_id"], unique=False
    )
    op.create_index(
        op.f("ix_audit_jobs_status"), "audit_jobs", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_audit_jobs_worker_id"), "audit_jobs", ["worker_id"], unique=False
    )
    # Composite index for claim query (status + available_at)
    op.create_index(
        "ix_audit_jobs_status_available_at",
        "audit_jobs",
        ["status", "available_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_audit_jobs_status_available_at", table_name="audit_jobs")
    op.drop_index(op.f("ix_audit_jobs_worker_id"), table_name="audit_jobs")
    op.drop_index(op.f("ix_audit_jobs_status"), table_name="audit_jobs")
    op.drop_index(op.f("ix_audit_jobs_audit_id"), table_name="audit_jobs")
    op.drop_table("audit_jobs")