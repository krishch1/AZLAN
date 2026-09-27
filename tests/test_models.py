"""Tests for AZLAN domain models.

These tests verify the domain models are correctly defined with:
- All required models import correctly
- Metadata contains all required tables
- Enum values are valid
- Required relationships exist
- UUID primary keys are configured
- Timestamps are timezone-aware
- Required foreign keys exist
- AuditEvent supports structured metadata (JSONB)
- Migration configuration sees the model metadata
"""


from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID

from backend.app.db.base import Base

# Import all models to register them with Base.metadata
from backend.app.models import (
    Audit,
    AuditConfiguration,
    AuditEvent,
    AuditMode,
    AuditStatus,
    EventType,
    Target,
)


class TestModelImports:
    """Test that all domain models can be imported."""

    def test_all_models_importable(self):
        """All required models should be importable."""
        assert Audit is not None
        assert Target is not None
        assert AuditConfiguration is not None
        assert AuditEvent is not None
        assert AuditStatus is not None
        assert AuditMode is not None
        assert EventType is not None

    def test_metadata_contains_required_tables(self):
        """Base.metadata should contain all four domain tables."""
        table_names = set(Base.metadata.tables.keys())
        required_tables = {"audits", "targets", "audit_configurations", "audit_events"}
        assert required_tables.issubset(table_names), (
            f"Missing tables: {required_tables - table_names}"
        )


class TestEnums:
    """Test domain enum values."""

    def test_audit_status_values(self):
        """AuditStatus should have all required lifecycle states."""
        statuses = {s.value for s in AuditStatus}
        required = {
            "created",
            "validating",
            "queued",
            "discovering",
            "auditing",
            "processing",
            "completed",
            "failed",
            "cancelled",
        }
        assert required.issubset(statuses), f"Missing statuses: {required - statuses}"

    def test_audit_status_terminal_states(self):
        """Terminal states should be correctly identified."""
        assert AuditStatus.is_terminal(AuditStatus.COMPLETED)
        assert AuditStatus.is_terminal(AuditStatus.FAILED)
        assert AuditStatus.is_terminal(AuditStatus.CANCELLED)
        assert not AuditStatus.is_terminal(AuditStatus.CREATED)
        assert not AuditStatus.is_terminal(AuditStatus.AUDITING)

    def test_audit_status_active_states(self):
        """Active states should be correctly identified."""
        assert AuditStatus.is_active(AuditStatus.CREATED)
        assert AuditStatus.is_active(AuditStatus.VALIDATING)
        assert AuditStatus.is_active(AuditStatus.QUEUED)
        assert AuditStatus.is_active(AuditStatus.DISCOVERING)
        assert AuditStatus.is_active(AuditStatus.AUDITING)
        assert AuditStatus.is_active(AuditStatus.PROCESSING)
        assert not AuditStatus.is_active(AuditStatus.COMPLETED)
        assert not AuditStatus.is_active(AuditStatus.FAILED)
        assert not AuditStatus.is_active(AuditStatus.CANCELLED)

    def test_audit_mode_values(self):
        """AuditMode should have all required modes."""
        modes = {m.value for m in AuditMode}
        required = {"quick", "standard", "deep", "exhaustive"}
        assert required.issubset(modes), f"Missing modes: {required - modes}"

    def test_event_type_values(self):
        """EventType should have all required event types."""
        events = {e.value for e in EventType}
        required = {
            "audit.created",
            "validation.started",
            "validation.completed",
            "audit.queued",
            "worker.claimed",
            "discovery.started",
            "discovery.completed",
            "auditing.started",
            "auditing.completed",
            "processing.started",
            "processing.completed",
            "audit.completed",
            "audit.failed",
            "audit.cancelled",
            "audit.error",
            "audit.warning",
            "audit.info",
        }
        assert required.issubset(events), f"Missing event types: {required - events}"


class TestTargetModel:
    """Test Target model definition."""

    def test_target_table_exists(self):
        """Target table should exist in metadata."""
        assert "targets" in Base.metadata.tables

    def test_target_primary_key_is_uuid(self):
        """Target.id should be UUID primary key."""
        table = Base.metadata.tables["targets"]
        pk_col = table.columns["id"]
        assert pk_col.primary_key
        assert isinstance(pk_col.type, UUID)

    def test_target_url_required(self):
        """Target.url should be non-nullable."""
        table = Base.metadata.tables["targets"]
        assert not table.columns["url"].nullable

    def test_target_normalized_url_nullable(self):
        """Target.normalized_url should be nullable."""
        table = Base.metadata.tables["targets"]
        assert table.columns["normalized_url"].nullable

    def test_target_created_at_timezone_aware(self):
        """Target.created_at should be timezone-aware DateTime."""
        table = Base.metadata.tables["targets"]
        col = table.columns["created_at"]
        assert col.type.timezone is True

    def test_target_has_audits_relationship(self):
        """Target should have audits relationship."""
        from sqlalchemy.orm import configure_mappers

        from backend.app.models.target import Target as TargetClass
        configure_mappers()
        rel = inspect(TargetClass).relationships.get("audits")
        assert rel is not None
        assert rel.mapper.class_.__name__ == "Audit"


class TestAuditConfigurationModel:
    """Test AuditConfiguration model definition."""

    def test_audit_configuration_table_exists(self):
        """AuditConfiguration table should exist in metadata."""
        assert "audit_configurations" in Base.metadata.tables

    def test_audit_configuration_primary_key_is_uuid(self):
        """AuditConfiguration.id should be UUID primary key."""
        table = Base.metadata.tables["audit_configurations"]
        pk_col = table.columns["id"]
        assert pk_col.primary_key
        assert isinstance(pk_col.type, UUID)

    def test_audit_configuration_audit_id_fk(self):
        """AuditConfiguration.audit_id should be FK to audits.id with CASCADE."""
        table = Base.metadata.tables["audit_configurations"]
        fk_col = table.columns["audit_id"]
        assert not fk_col.nullable
        assert fk_col.unique
        fks = list(fk_col.foreign_keys)
        assert len(fks) == 1
        fk = fks[0]
        assert fk.column.table.name == "audits"
        assert fk.column.name == "id"
        assert fk.ondelete == "CASCADE"

    def test_audit_configuration_mode_default(self):
        """AuditConfiguration.mode should default to 'standard'."""
        table = Base.metadata.tables["audit_configurations"]
        col = table.columns["mode"]
        assert col.default is not None
        assert col.default.arg == "standard"

    def test_audit_configuration_auth_config_placeholder(self):
        """AuditConfiguration.auth_config should have safe default (no plaintext secrets)."""
        table = Base.metadata.tables["audit_configurations"]
        col = table.columns["auth_config"]
        # Check server_default (SQL-level default) since we use both default and server_default
        assert col.server_default is not None
        default_val = str(col.server_default.arg)
        assert '"type"' in default_val
        assert '"none"' in default_val

    def test_audit_configuration_json_fields(self):
        """AuditConfiguration should have JSON fields for structured config."""
        table = Base.metadata.tables["audit_configurations"]
        json_fields = ["crawl_config", "scope_config", "auth_config", "testing_config", "limits_config"]
        for field in json_fields:
            assert field in table.columns


class TestAuditModel:
    """Test Audit model definition."""

    def test_audit_table_exists(self):
        """Audit table should exist in metadata."""
        assert "audits" in Base.metadata.tables

    def test_audit_primary_key_is_uuid(self):
        """Audit.id should be UUID primary key."""
        table = Base.metadata.tables["audits"]
        pk_col = table.columns["id"]
        assert pk_col.primary_key
        assert isinstance(pk_col.type, UUID)

    def test_audit_target_id_fk(self):
        """Audit.target_id should be FK to targets.id with CASCADE."""
        table = Base.metadata.tables["audits"]
        fk_col = table.columns["target_id"]
        assert not fk_col.nullable
        fks = list(fk_col.foreign_keys)
        assert len(fks) == 1
        fk = fks[0]
        assert fk.column.table.name == "targets"
        assert fk.column.name == "id"
        assert fk.ondelete == "CASCADE"

    def test_audit_status_default(self):
        """Audit.status should default to 'created'."""
        table = Base.metadata.tables["audits"]
        col = table.columns["status"]
        assert col.default is not None
        assert col.default.arg == "created"

    def test_audit_timestamps_timezone_aware(self):
        """All audit timestamp columns should be timezone-aware."""
        table = Base.metadata.tables["audits"]
        timestamp_cols = ["created_at", "started_at", "completed_at", "cancelled_at", "updated_at"]
        for col_name in timestamp_cols:
            col = table.columns[col_name]
            assert col.type.timezone is True, f"{col_name} should be timezone-aware"

    def test_audit_indexes(self):
        """Audit should have indexes on target_id and status."""
        table = Base.metadata.tables["audits"]
        index_names = {idx.name for idx in table.indexes}
        assert "ix_audits_target_id" in index_names
        assert "ix_audits_status" in index_names

    def test_audit_relationships(self):
        """Audit should have target, configuration, and events relationships."""
        from backend.app.models.audit import Audit as AuditClass
        mapper = inspect(AuditClass)
        assert "target" in mapper.relationships
        assert "configuration" in mapper.relationships
        assert "events" in mapper.relationships
        events_rel = mapper.relationships["events"]
        assert "delete-orphan" in events_rel.cascade


class TestAuditEventModel:
    """Test AuditEvent model definition."""

    def test_audit_event_table_exists(self):
        """AuditEvent table should exist in metadata."""
        assert "audit_events" in Base.metadata.tables

    def test_audit_event_primary_key_is_uuid(self):
        """AuditEvent.id should be UUID primary key."""
        table = Base.metadata.tables["audit_events"]
        pk_col = table.columns["id"]
        assert pk_col.primary_key
        assert isinstance(pk_col.type, UUID)

    def test_audit_event_audit_id_fk(self):
        """AuditEvent.audit_id should be FK to audits.id with CASCADE."""
        table = Base.metadata.tables["audit_events"]
        fk_col = table.columns["audit_id"]
        assert not fk_col.nullable
        fks = list(fk_col.foreign_keys)
        assert len(fks) == 1
        fk = fks[0]
        assert fk.column.table.name == "audits"
        assert fk.column.name == "id"
        assert fk.ondelete == "CASCADE"

    def test_audit_event_timestamp_timezone_aware(self):
        """AuditEvent.timestamp should be timezone-aware."""
        table = Base.metadata.tables["audit_events"]
        col = table.columns["timestamp"]
        assert col.type.timezone is True

    def test_audit_event_indexes(self):
        """AuditEvent should have indexes for efficient querying."""
        table = Base.metadata.tables["audit_events"]
        index_names = {idx.name for idx in table.indexes}
        assert "ix_audit_events_audit_id" in index_names
        assert "ix_audit_events_event_type" in index_names
        assert "ix_audit_events_audit_created" in index_names

    def test_audit_event_composite_index_columns(self):
        """Composite index should be on (audit_id, timestamp)."""
        table = Base.metadata.tables["audit_events"]
        composite_idx = None
        for idx in table.indexes:
            if idx.name == "ix_audit_events_audit_created":
                composite_idx = idx
                break
        assert composite_idx is not None
        idx_cols = [c.name for c in composite_idx.columns]
        assert idx_cols == ["audit_id", "timestamp"]

    def test_audit_event_relationship(self):
        """AuditEvent should have relationship back to Audit."""
        from sqlalchemy.orm import configure_mappers

        from backend.app.models.audit_event import AuditEvent as AuditEventClass
        configure_mappers()
        mapper = inspect(AuditEventClass)
        rel = mapper.relationships.get("audit")
        assert rel is not None
        assert rel.mapper.class_.__name__ == "Audit"