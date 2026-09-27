"""Create audit domain models

Revision ID: 001
Revises: 
Create Date: 2026-09-26 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. targets table
    op.create_table(
        "targets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            comment="Unique identifier for the target",
        ),
        sa.Column(
            "url",
            sa.Text(),
            nullable=False,
            comment="Original target URL provided by the user",
        ),
        sa.Column(
            "normalized_url",
            sa.Text(),
            nullable=True,
            comment="Canonical/normalized representation of the URL (if computed)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            comment="When the target was registered",
        ),
    )

    # 2. audits table
    op.create_table(
        "audits",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            comment="Unique identifier for the audit",
        ),
        sa.Column(
            "target_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("targets.id", ondelete="CASCADE"),
            nullable=False,
            comment="The target being audited",
        ),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="created",
            comment="Current lifecycle status",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            comment="When the audit was created",
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When the audit started processing",
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When the audit completed successfully",
        ),
        sa.Column(
            "cancelled_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When the audit was cancelled",
        ),
        sa.Column(
            "failure_info",
            sa.Text(),
            nullable=True,
            comment="Structured failure information (JSON-encoded) if the audit failed",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            comment="Last timestamp update for lifecycle tracking",
        ),
    )

    op.create_index("ix_audits_target_id", "audits", ["target_id"])
    op.create_index("ix_audits_status", "audits", ["status"])

    # 3. audit_configurations table
    op.create_table(
        "audit_configurations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            comment="Unique identifier for the audit configuration",
        ),
        sa.Column(
            "audit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("audits.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
            comment="The audit this configuration belongs to",
        ),
        sa.Column(
            "mode",
            sa.String(50),
            nullable=False,
            server_default="standard",
            comment="Audit execution mode (quick, standard, deep, exhaustive)",
        ),
        sa.Column(
            "max_pages",
            sa.Text(),
            nullable=True,
            comment="JSON-encoded crawl limits (e.g., max_pages, max_depth)",
        ),
        sa.Column(
            "crawl_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Structured crawl/discovery configuration",
        ),
        sa.Column(
            "scope_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Scope configuration: include/exclude patterns, allowed_domains, etc.",
        ),
        sa.Column(
            "auth_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{\"type\": \"none\"}'"),
            comment="SAFE PLACEHOLDER for authentication configuration. Never store plaintext credentials. Use secret references.",
        ),
        sa.Column(
            "testing_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Active testing configuration (which checks to run, etc.)",
        ),
        sa.Column(
            "limits_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Resource and request limits (timeouts, concurrency, etc.)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            comment="When the configuration was created",
        ),
    )

    # 4. audit_events table
    op.create_table(
        "audit_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            comment="Unique identifier for the event",
        ),
        sa.Column(
            "audit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("audits.id", ondelete="CASCADE"),
            nullable=False,
            comment="The audit this event belongs to",
        ),
        sa.Column(
            "event_type",
            sa.String(100),
            nullable=False,
            comment="Type of event (from EventType enum)",
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            comment="When the event occurred",
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Structured event metadata (JSONB). Never store secrets here.",
        ),
    )

    op.create_index("ix_audit_events_audit_id", "audit_events", ["audit_id"])
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"])
    op.create_index("ix_audit_events_audit_created", "audit_events", ["audit_id", "timestamp"])


def downgrade() -> None:
    op.drop_index("ix_audit_events_audit_created", table_name="audit_events")
    op.drop_index("ix_audit_events_event_type", table_name="audit_events")
    op.drop_index("ix_audit_events_audit_id", table_name="audit_events")
    op.drop_table("audit_events")

    op.drop_table("audit_configurations")

    op.drop_index("ix_audits_status", table_name="audits")
    op.drop_index("ix_audits_target_id", table_name="audits")
    op.drop_table("audits")

    op.drop_table("targets")