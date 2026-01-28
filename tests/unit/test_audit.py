"""Unit tests for the audit logging module."""

import pytest
from datetime import datetime

from fhir_r4_mcp.audit import (
    AuditAction,
    AuditAgent,
    AuditConfig,
    AuditEntity,
    AuditEvent,
    AuditLogger,
    AuditOutcome,
    AuditSource,
    AuditSubtype,
    AuditType,
)
from fhir_r4_mcp.audit.events import create_audit_event


class TestAuditEvent:
    """Tests for AuditEvent class."""

    def test_audit_event_creation(self):
        """Test basic audit event creation."""
        event = AuditEvent(
            type=AuditType.REST,
            subtype=AuditSubtype.READ,
            action=AuditAction.READ,
            outcome=AuditOutcome.SUCCESS,
        )

        assert event.type == AuditType.REST
        assert event.subtype == AuditSubtype.READ
        assert event.action == AuditAction.READ
        assert event.outcome == AuditOutcome.SUCCESS
        assert event.recorded is not None

    def test_audit_event_to_fhir(self):
        """Test conversion to FHIR AuditEvent format."""
        agent = AuditAgent(
            who="user123",
            name="Test User",
            requestor=True,
        )

        entity = AuditEntity(
            what="Patient/123",
            type_code="2",
            role_code="1",
        )

        event = AuditEvent(
            type=AuditType.REST,
            subtype=AuditSubtype.READ,
            action=AuditAction.READ,
            outcome=AuditOutcome.SUCCESS,
            agent=agent,
            entity=[entity],
        )

        fhir = event.to_fhir()

        assert fhir["resourceType"] == "AuditEvent"
        assert fhir["type"]["code"] == "rest"
        assert fhir["action"] == "R"
        assert fhir["outcome"] == "0"
        assert len(fhir["agent"]) == 1
        assert len(fhir["entity"]) == 1

    def test_audit_event_to_dict(self):
        """Test conversion to simple dictionary format."""
        event = AuditEvent(
            type=AuditType.QUERY,
            subtype=AuditSubtype.SEARCH,
            action=AuditAction.READ,
            outcome=AuditOutcome.SUCCESS,
        )

        data = event.to_dict()

        assert data["type"] == "query"
        assert data["subtype"] == "search"
        assert data["action"] == "R"
        assert data["outcome"] == "0"


class TestAuditAgent:
    """Tests for AuditAgent class."""

    def test_agent_creation(self):
        """Test agent creation."""
        agent = AuditAgent(
            who="user123",
            name="Test User",
            role=["admin"],
            network_address="192.168.1.1",
        )

        assert agent.who == "user123"
        assert agent.name == "Test User"
        assert "admin" in agent.role

    def test_agent_to_fhir(self):
        """Test agent conversion to FHIR format."""
        agent = AuditAgent(
            who="user123",
            name="Test User",
            network_address="192.168.1.1",
            network_type="2",
        )

        fhir = agent.to_fhir()

        assert fhir["who"]["display"] == "Test User"
        assert fhir["requestor"] is True
        assert fhir["network"]["address"] == "192.168.1.1"


class TestAuditEntity:
    """Tests for AuditEntity class."""

    def test_entity_creation(self):
        """Test entity creation."""
        entity = AuditEntity(
            what="Patient/123",
            type_code="2",
            name="Test Patient",
        )

        assert entity.what == "Patient/123"
        assert entity.type_code == "2"

    def test_entity_to_fhir(self):
        """Test entity conversion to FHIR format."""
        entity = AuditEntity(
            what="Patient/123",
            type_code="2",
            role_code="1",
            detail={"action": "read"},
        )

        fhir = entity.to_fhir()

        assert fhir["what"]["reference"] == "Patient/123"
        assert fhir["type"]["code"] == "2"
        assert fhir["role"]["code"] == "1"
        assert len(fhir["detail"]) == 1


class TestCreateAuditEvent:
    """Tests for the create_audit_event factory function."""

    def test_create_read_event(self):
        """Test creating a read audit event."""
        event = create_audit_event(
            subtype=AuditSubtype.READ,
            outcome=AuditOutcome.SUCCESS,
            connection_id="test-conn",
            resource_type="Patient",
            resource_id="123",
        )

        assert event.subtype == AuditSubtype.READ
        assert event.action == AuditAction.READ
        assert event.outcome == AuditOutcome.SUCCESS
        assert len(event.entity) == 1
        assert event.entity[0].what == "Patient/123"

    def test_create_search_event(self):
        """Test creating a search audit event."""
        event = create_audit_event(
            subtype=AuditSubtype.SEARCH,
            outcome=AuditOutcome.SUCCESS,
            connection_id="test-conn",
            resource_type="Observation",
            query="patient=123&code=vital-signs",
        )

        assert event.subtype == AuditSubtype.SEARCH
        assert event.type == AuditType.QUERY
        assert len(event.entity) == 1

    def test_create_failure_event(self):
        """Test creating a failure audit event."""
        event = create_audit_event(
            subtype=AuditSubtype.READ,
            outcome=AuditOutcome.SERIOUS_FAILURE,
            connection_id="test-conn",
            resource_type="Patient",
            resource_id="123",
            outcome_desc="Resource not found",
        )

        assert event.outcome == AuditOutcome.SERIOUS_FAILURE
        assert event.outcome_desc == "Resource not found"


class TestAuditConfig:
    """Tests for AuditConfig class."""

    def test_default_config(self):
        """Test default configuration."""
        config = AuditConfig()

        assert config.enabled is True
        assert config.output == "file"
        assert config.async_logging is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = AuditConfig(
            enabled=False,
            output="stdout",
            file_path="/tmp/audit.log",
        )

        assert config.enabled is False
        assert config.output == "stdout"
        assert config.file_path == "/tmp/audit.log"


class TestAuditLogger:
    """Tests for AuditLogger class."""

    @pytest.fixture
    def logger(self):
        """Create a test logger."""
        config = AuditConfig(enabled=True, output="none")
        return AuditLogger(config)

    def test_logger_creation(self, logger):
        """Test logger creation."""
        assert logger.enabled is True

    @pytest.mark.asyncio
    async def test_log_operation(self, logger):
        """Test logging an operation."""
        await logger.log_operation(
            subtype=AuditSubtype.READ,
            outcome=AuditOutcome.SUCCESS,
            connection_id="test-conn",
            resource_type="Patient",
            resource_id="123",
        )

        # Since output is "none", this should just not error

    @pytest.mark.asyncio
    async def test_disabled_logger(self):
        """Test that disabled logger doesn't log."""
        config = AuditConfig(enabled=False)
        logger = AuditLogger(config)

        # Should not error even when disabled
        await logger.log_operation(
            subtype=AuditSubtype.READ,
            outcome=AuditOutcome.SUCCESS,
            connection_id="test-conn",
        )
