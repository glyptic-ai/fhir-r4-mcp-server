"""Unit tests for the CDS Hooks module."""

import pytest

from fhir_r4_mcp.cds import (
    CDSCard,
    CDSHook,
    CDSHookRequest,
    CDSHookResponse,
    CDSLink,
    CDSSuggestion,
    HookType,
)
from fhir_r4_mcp.cds.hooks import (
    CardIndicator,
    CDSAction,
    SelectionBehavior,
)
from fhir_r4_mcp.cds.service import CDSServiceDiscovery


class TestHookType:
    """Tests for HookType enum."""

    def test_hook_types(self):
        """Test hook type values."""
        assert HookType.PATIENT_VIEW.value == "patient-view"
        assert HookType.MEDICATION_PRESCRIBE.value == "medication-prescribe"
        assert HookType.ORDER_SIGN.value == "order-sign"


class TestCDSLink:
    """Tests for CDSLink class."""

    def test_link_creation(self):
        """Test link creation."""
        link = CDSLink(
            label="View Guidelines",
            url="https://example.com/guidelines",
            type="absolute",
        )

        assert link.label == "View Guidelines"
        assert link.type == "absolute"

    def test_link_to_dict(self):
        """Test link serialization."""
        link = CDSLink(
            label="Launch SMART App",
            url="https://example.com/app",
            type="smart",
            app_context="patient/123",
        )

        data = link.to_dict()

        assert data["label"] == "Launch SMART App"
        assert data["type"] == "smart"
        assert data["appContext"] == "patient/123"


class TestCDSAction:
    """Tests for CDSAction class."""

    def test_action_creation(self):
        """Test action creation."""
        action = CDSAction(
            type="create",
            description="Create MedicationRequest",
            resource={"resourceType": "MedicationRequest"},
        )

        assert action.type == "create"
        assert action.resource["resourceType"] == "MedicationRequest"

    def test_action_to_dict(self):
        """Test action serialization."""
        action = CDSAction(
            type="delete",
            description="Remove duplicate order",
            resource_id="order-123",
        )

        data = action.to_dict()

        assert data["type"] == "delete"
        assert data["resourceId"] == "order-123"


class TestCDSSuggestion:
    """Tests for CDSSuggestion class."""

    def test_suggestion_creation(self):
        """Test suggestion creation."""
        suggestion = CDSSuggestion(
            label="Prescribe alternative medication",
            is_recommended=True,
        )

        assert suggestion.label == "Prescribe alternative medication"
        assert suggestion.is_recommended is True

    def test_suggestion_with_actions(self):
        """Test suggestion with actions."""
        action = CDSAction(
            type="create",
            description="Create prescription",
            resource={"resourceType": "MedicationRequest"},
        )

        suggestion = CDSSuggestion(
            label="Accept recommendation",
            actions=[action],
        )

        data = suggestion.to_dict()

        assert len(data["actions"]) == 1
        assert data["actions"][0]["type"] == "create"


class TestCDSCard:
    """Tests for CDSCard class."""

    def test_card_creation(self):
        """Test card creation."""
        card = CDSCard(
            summary="Drug interaction detected",
            indicator=CardIndicator.WARNING,
            detail="Potential interaction between medications X and Y",
        )

        assert card.summary == "Drug interaction detected"
        assert card.indicator == CardIndicator.WARNING

    def test_card_to_dict(self):
        """Test card serialization."""
        card = CDSCard(
            summary="Review patient allergies",
            indicator=CardIndicator.INFO,
            source={"label": "Allergy Checker", "url": "https://example.com"},
            links=[CDSLink(label="Details", url="https://example.com/details")],
        )

        data = card.to_dict()

        assert data["summary"] == "Review patient allergies"
        assert data["indicator"] == "info"
        assert data["source"]["label"] == "Allergy Checker"
        assert len(data["links"]) == 1

    def test_critical_card(self):
        """Test critical indicator card."""
        card = CDSCard(
            summary="Critical allergy alert!",
            indicator=CardIndicator.CRITICAL,
            override_reasons=[
                {"code": "patient-request", "display": "Patient requested override"}
            ],
        )

        data = card.to_dict()

        assert data["indicator"] == "critical"
        assert len(data["overrideReasons"]) == 1


class TestCDSHook:
    """Tests for CDSHook class."""

    def test_hook_creation(self):
        """Test hook creation."""
        hook = CDSHook(
            id="drug-interaction-check",
            hook=HookType.MEDICATION_PRESCRIBE,
            title="Drug Interaction Checker",
            description="Checks for potential drug interactions",
            prefetch={
                "patient": "Patient/{{context.patientId}}",
                "medications": "MedicationRequest?patient={{context.patientId}}",
            },
        )

        assert hook.id == "drug-interaction-check"
        assert hook.hook == HookType.MEDICATION_PRESCRIBE

    def test_hook_to_dict(self):
        """Test hook serialization."""
        hook = CDSHook(
            id="patient-risk-alert",
            hook=HookType.PATIENT_VIEW,
            title="Patient Risk Alert",
            description="Alerts on patient risk factors",
        )

        data = hook.to_dict()

        assert data["id"] == "patient-risk-alert"
        assert data["hook"] == "patient-view"
        assert data["title"] == "Patient Risk Alert"


class TestCDSHookRequest:
    """Tests for CDSHookRequest class."""

    def test_request_creation(self):
        """Test request creation."""
        request = CDSHookRequest(
            hook="patient-view",
            hook_instance="12345",
            context={
                "userId": "Practitioner/123",
                "patientId": "Patient/456",
                "encounterId": "Encounter/789",
            },
        )

        assert request.hook == "patient-view"
        assert request.get_patient_id() == "Patient/456"

    def test_from_dict(self):
        """Test parsing from dictionary."""
        data = {
            "hook": "medication-prescribe",
            "hookInstance": "abc123",
            "context": {
                "userId": "Practitioner/123",
                "patientId": "Patient/456",
                "medications": {"resourceType": "Bundle"},
            },
            "prefetch": {
                "patient": {"resourceType": "Patient", "id": "456"},
            },
            "fhirServer": "https://example.com/fhir",
        }

        request = CDSHookRequest.from_dict(data)

        assert request.hook == "medication-prescribe"
        assert request.hook_instance == "abc123"
        assert request.get_patient_id() == "Patient/456"
        assert request.fhir_server == "https://example.com/fhir"

    def test_get_patient_id_variations(self):
        """Test patient ID extraction from various formats."""
        # Standard patientId
        request1 = CDSHookRequest(
            hook="test",
            hook_instance="123",
            context={"patientId": "pat-123"},
        )
        assert request1.get_patient_id() == "pat-123"

        # Using 'patient' key
        request2 = CDSHookRequest(
            hook="test",
            hook_instance="123",
            context={"patient": "pat-456"},
        )
        assert request2.get_patient_id() == "pat-456"

        # Missing patient
        request3 = CDSHookRequest(
            hook="test",
            hook_instance="123",
            context={},
        )
        assert request3.get_patient_id() is None


class TestCDSHookResponse:
    """Tests for CDSHookResponse class."""

    def test_response_creation(self):
        """Test response creation."""
        response = CDSHookResponse()

        assert response.cards == []
        assert response.system_actions == []

    def test_add_card(self):
        """Test adding a card to response."""
        response = CDSHookResponse()

        card = response.add_card(
            summary="Test card",
            indicator=CardIndicator.INFO,
            detail="Some details",
        )

        assert len(response.cards) == 1
        assert card.summary == "Test card"

    def test_add_info_card(self):
        """Test adding info card shortcut."""
        response = CDSHookResponse()

        response.add_info_card("Information", "Details here")

        assert len(response.cards) == 1
        assert response.cards[0].indicator == CardIndicator.INFO

    def test_add_warning_card(self):
        """Test adding warning card shortcut."""
        response = CDSHookResponse()

        response.add_warning_card("Warning", "Be careful")

        assert response.cards[0].indicator == CardIndicator.WARNING

    def test_add_critical_card(self):
        """Test adding critical card shortcut."""
        response = CDSHookResponse()

        response.add_critical_card("Alert!", "Immediate action required")

        assert response.cards[0].indicator == CardIndicator.CRITICAL

    def test_response_to_dict(self):
        """Test response serialization."""
        response = CDSHookResponse()
        response.add_info_card("Test", "Details")
        response.system_actions.append(
            CDSAction(type="create", description="Auto-create", resource={})
        )

        data = response.to_dict()

        assert len(data["cards"]) == 1
        assert len(data["systemActions"]) == 1


class TestCDSServiceDiscovery:
    """Tests for CDSServiceDiscovery class."""

    def test_discovery_from_dict(self):
        """Test parsing discovery response."""
        data = {
            "services": [
                {
                    "id": "patient-risk",
                    "hook": "patient-view",
                    "title": "Patient Risk Assessment",
                    "description": "Assesses patient risk factors",
                },
                {
                    "id": "drug-check",
                    "hook": "medication-prescribe",
                    "title": "Drug Interaction Checker",
                    "description": "Checks for drug interactions",
                    "prefetch": {
                        "medications": "MedicationRequest?patient={{context.patientId}}",
                    },
                },
            ]
        }

        discovery = CDSServiceDiscovery.from_dict(data)

        assert len(discovery.services) == 2

    def test_get_service(self):
        """Test getting a service by ID."""
        data = {
            "services": [
                {
                    "id": "test-service",
                    "hook": "patient-view",
                    "title": "Test",
                    "description": "Test service",
                }
            ]
        }

        discovery = CDSServiceDiscovery.from_dict(data)

        service = discovery.get_service("test-service")

        assert service is not None
        assert service.id == "test-service"

    def test_get_nonexistent_service(self):
        """Test getting a nonexistent service."""
        discovery = CDSServiceDiscovery()

        service = discovery.get_service("nonexistent")

        assert service is None

    def test_get_services_by_hook(self):
        """Test filtering services by hook type."""
        data = {
            "services": [
                {"id": "s1", "hook": "patient-view", "title": "S1", "description": ""},
                {"id": "s2", "hook": "patient-view", "title": "S2", "description": ""},
                {"id": "s3", "hook": "medication-prescribe", "title": "S3", "description": ""},
            ]
        }

        discovery = CDSServiceDiscovery.from_dict(data)

        patient_view_services = discovery.get_services_by_hook(HookType.PATIENT_VIEW)

        assert len(patient_view_services) == 2
