"""Pytest configuration and fixtures for FHIR R4 MCP Server tests."""

import os

import pytest


@pytest.fixture
def sample_patient() -> dict:
    """Sample FHIR Patient resource for testing."""
    return {
        "resourceType": "Patient",
        "id": "test-patient-1",
        "active": True,
        "name": [
            {
                "use": "official",
                "family": "Smith",
                "given": ["John", "Michael"],
            }
        ],
        "gender": "male",
        "birthDate": "1980-01-15",
        "identifier": [
            {
                "system": "http://example.org/mrn",
                "value": "MRN12345",
            }
        ],
    }


@pytest.fixture
def sample_bundle(sample_patient) -> dict:
    """Sample FHIR Bundle for testing."""
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": 1,
        "entry": [
            {
                "fullUrl": "http://example.org/Patient/test-patient-1",
                "resource": sample_patient,
            }
        ],
    }


@pytest.fixture
def fhir_test_config() -> dict:
    """
    Get FHIR test configuration from environment variables.

    Returns empty dict if required vars not set (skip integration tests).
    """
    base_url = os.environ.get("FHIR_TEST_BASE_URL")
    client_id = os.environ.get("FHIR_TEST_CLIENT_ID")
    private_key_path = os.environ.get("FHIR_TEST_PRIVATE_KEY_PATH")

    if not all([base_url, client_id, private_key_path]):
        return {}

    return {
        "base_url": base_url,
        "client_id": client_id,
        "private_key_path": private_key_path,
    }


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (requires FHIR server)"
    )
