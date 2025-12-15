"""FHIR R4 MCP Server - Main server implementation with all 20 tools."""

import time
from enum import Enum
from typing import Any

from mcp.server.fastmcp import FastMCP

from fhir_r4_mcp.core.client import fhir_client
from fhir_r4_mcp.core.connection_manager import (
    ConnectionManager,
    VendorType,
    connection_manager,
)
from fhir_r4_mcp.core.response_processor import response_processor
from fhir_r4_mcp.utils.errors import FHIRError
from fhir_r4_mcp.utils.logging import get_logger

logger = get_logger(__name__)


# Supported FHIR R4 resource types
class ResourceType(str, Enum):
    """Supported FHIR R4 resource types."""

    ALLERGY_INTOLERANCE = "AllergyIntolerance"
    CARE_PLAN = "CarePlan"
    CARE_TEAM = "CareTeam"
    CONDITION = "Condition"
    DEVICE = "Device"
    DIAGNOSTIC_REPORT = "DiagnosticReport"
    DOCUMENT_REFERENCE = "DocumentReference"
    ENCOUNTER = "Encounter"
    GOAL = "Goal"
    IMMUNIZATION = "Immunization"
    LOCATION = "Location"
    MEDICATION = "Medication"
    MEDICATION_REQUEST = "MedicationRequest"
    MEDICATION_STATEMENT = "MedicationStatement"
    OBSERVATION = "Observation"
    ORGANIZATION = "Organization"
    PATIENT = "Patient"
    PRACTITIONER = "Practitioner"
    PROCEDURE = "Procedure"
    PROVENANCE = "Provenance"
    SERVICE_REQUEST = "ServiceRequest"


# Clinical note types with LOINC codes
NOTE_TYPE_LOINC = {
    "progress": "11506-3",
    "discharge": "18842-5",
    "history": "34117-2",
    "consult": "11488-4",
    "procedure": "28570-0",
}


def create_server() -> FastMCP:
    """
    Create and configure the FHIR R4 MCP Server.

    Returns:
        Configured FastMCP server instance with all 20 tools.
    """
    mcp = FastMCP(
        "FHIR R4 MCP Server",
        version="0.1.0",
        description="AI-agnostic Model Context Protocol server for FHIR R4 EHR integration",
    )

    # ==========================================================================
    # Category 1: Connection Management (3 tools)
    # ==========================================================================

    @mcp.tool()
    async def fhir_connect(
        connection_id: str,
        base_url: str,
        auth_type: str,
        client_id: str | None = None,
        private_key_pem: str | None = None,
        jwks_url: str | None = None,
        api_key: str | None = None,
        username: str | None = None,
        password: str | None = None,
        vendor: str = "generic",
        scope: str = "system/*.read",
    ) -> dict[str, Any]:
        """
        Register and authenticate with a FHIR server.

        Args:
            connection_id: Unique identifier for this connection
            base_url: FHIR server base URL
            auth_type: Authentication type (smart_backend, oauth2, basic, api_key)
            client_id: Client ID for OAuth/SMART auth
            private_key_pem: PEM-encoded private key or path to key file (for SMART Backend)
            jwks_url: Public JWKS endpoint URL
            api_key: API key for API key auth
            username: Username for basic auth
            password: Password for basic auth
            vendor: EHR vendor (nextgen, epic, cerner, generic)
            scope: OAuth scope (default: system/*.read)

        Returns:
            Connection status with token expiry and capabilities
        """
        start_time = time.time()
        try:
            # Build auth config based on auth type
            auth_config: dict[str, Any] = {}

            if auth_type == "smart_backend":
                if not client_id or not private_key_pem:
                    raise ValueError("smart_backend auth requires client_id and private_key_pem")
                # Need to determine token_endpoint from base_url
                token_endpoint = f"{base_url.rstrip('/')}/oauth2/token"
                auth_config = {
                    "client_id": client_id,
                    "private_key_pem": private_key_pem,
                    "token_endpoint": token_endpoint,
                    "scope": scope,
                }
                if jwks_url:
                    auth_config["jwks_url"] = jwks_url

            elif auth_type == "api_key":
                if not api_key:
                    raise ValueError("api_key auth requires api_key")
                auth_config = {"api_key": api_key}

            elif auth_type == "basic":
                if not username or not password:
                    raise ValueError("basic auth requires username and password")
                auth_config = {"username": username, "password": password}

            connection = await connection_manager.connect(
                connection_id=connection_id,
                base_url=base_url,
                auth_type=auth_type,
                vendor=vendor,
                **auth_config,
            )

            duration_ms = int((time.time() - start_time) * 1000)
            return response_processor.create_success_response(
                data=connection.to_dict(),
                connection_id=connection_id,
                duration_ms=duration_ms,
            )

        except FHIRError as e:
            return response_processor.create_error_response(e, connection_id)
        except Exception as e:
            logger.exception(f"Unexpected error in fhir_connect: {e}")
            return response_processor.create_error_response(e, connection_id)

    @mcp.tool()
    async def fhir_disconnect(connection_id: str) -> dict[str, Any]:
        """
        Remove a registered FHIR server connection.

        Args:
            connection_id: Connection to remove

        Returns:
            Success status
        """
        try:
            removed = await connection_manager.disconnect(connection_id)
            return response_processor.create_success_response(
                data={"removed": removed, "connection_id": connection_id},
                connection_id=connection_id,
            )
        except FHIRError as e:
            return response_processor.create_error_response(e, connection_id)

    @mcp.tool()
    async def fhir_list_connections() -> dict[str, Any]:
        """
        List all active FHIR server connections with their status.

        Returns:
            Array of connection objects with health status
        """
        connections = connection_manager.list_connections()
        return response_processor.create_success_response(
            data={"connections": connections, "count": len(connections)},
            connection_id="system",
        )

    # ==========================================================================
    # Category 2: Patient Operations (3 tools)
    # ==========================================================================

    @mcp.tool()
    async def fhir_patient_search(
        connection_id: str,
        family: str | None = None,
        given: str | None = None,
        birthdate: str | None = None,
        identifier: str | None = None,
        gender: str | None = None,
        _count: int = 100,
        active_only: bool = True,
    ) -> dict[str, Any]:
        """
        Search for patients matching criteria.

        Args:
            connection_id: Which FHIR server to query
            family: Family/last name
            given: Given/first name
            birthdate: Date of birth (YYYY-MM-DD)
            identifier: MRN or other identifier
            gender: Gender (male, female, other, unknown)
            _count: Maximum results (default 100)
            active_only: Only return active patients (default true)

        Returns:
            FHIR Bundle of Patient resources
        """
        start_time = time.time()
        try:
            params: dict[str, Any] = {"_count": _count}

            if family:
                params["family"] = family
            if given:
                params["given"] = given
            if birthdate:
                params["birthdate"] = birthdate
            if identifier:
                params["identifier"] = identifier
            if gender:
                params["gender"] = gender
            if active_only:
                params["active"] = "true"

            result = await fhir_client.search(connection_id, "Patient", params)

            duration_ms = int((time.time() - start_time) * 1000)
            return response_processor.parse_search_result(result, connection_id, duration_ms)

        except FHIRError as e:
            return response_processor.create_error_response(e, connection_id)

    @mcp.tool()
    async def fhir_patient_read(
        connection_id: str,
        patient_id: str,
    ) -> dict[str, Any]:
        """
        Get a single patient by ID.

        Args:
            connection_id: Which FHIR server
            patient_id: FHIR Patient resource ID

        Returns:
            Complete Patient resource
        """
        start_time = time.time()
        try:
            result = await fhir_client.read(connection_id, "Patient", patient_id)
            duration_ms = int((time.time() - start_time) * 1000)
            return response_processor.parse_resource(result, connection_id, duration_ms)

        except FHIRError as e:
            return response_processor.create_error_response(e, connection_id)

    @mcp.tool()
    async def fhir_patient_everything(
        connection_id: str,
        patient_id: str,
        start: str | None = None,
        end: str | None = None,
        _type: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get all data for a patient ($everything operation).

        Args:
            connection_id: Which FHIR server
            patient_id: FHIR Patient resource ID
            start: Start date filter (YYYY-MM-DD)
            end: End date filter (YYYY-MM-DD)
            _type: Resource types to include

        Returns:
            FHIR Bundle with all patient data
        """
        start_time = time.time()
        try:
            params: dict[str, Any] = {}
            if start:
                params["start"] = start
            if end:
                params["end"] = end
            if _type:
                params["_type"] = ",".join(_type)

            result = await fhir_client.get(
                connection_id,
                f"Patient/{patient_id}/$everything",
                params=params if params else None,
            )

            duration_ms = int((time.time() - start_time) * 1000)
            return response_processor.parse_search_result(result, connection_id, duration_ms)

        except FHIRError as e:
            return response_processor.create_error_response(e, connection_id)

    # ==========================================================================
    # Category 3: Clinical Resource Queries (2 tools)
    # ==========================================================================

    @mcp.tool()
    async def fhir_query(
        connection_id: str,
        resource_type: str,
        patient: str | None = None,
        parameters: dict[str, Any] | None = None,
        _count: int = 100,
        _include: list[str] | None = None,
        _revinclude: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Generic FHIR resource query.

        Args:
            connection_id: Which FHIR server
            resource_type: FHIR resource type (e.g., Condition, Observation)
            patient: Patient reference filter
            parameters: Additional search parameters
            _count: Maximum results
            _include: Related resources to include
            _revinclude: Reverse includes

        Returns:
            FHIR Bundle of matching resources
        """
        start_time = time.time()
        try:
            params: dict[str, Any] = {"_count": _count}

            if patient:
                params["patient"] = patient

            if parameters:
                params.update(parameters)

            if _include:
                params["_include"] = _include

            if _revinclude:
                params["_revinclude"] = _revinclude

            result = await fhir_client.search(connection_id, resource_type, params)

            duration_ms = int((time.time() - start_time) * 1000)
            return response_processor.parse_search_result(result, connection_id, duration_ms)

        except FHIRError as e:
            return response_processor.create_error_response(e, connection_id)

    @mcp.tool()
    async def fhir_resource_read(
        connection_id: str,
        resource_type: str,
        resource_id: str,
    ) -> dict[str, Any]:
        """
        Read a specific resource by ID.

        Args:
            connection_id: Which FHIR server
            resource_type: FHIR resource type
            resource_id: Resource ID

        Returns:
            Single FHIR resource
        """
        start_time = time.time()
        try:
            result = await fhir_client.read(connection_id, resource_type, resource_id)
            duration_ms = int((time.time() - start_time) * 1000)
            return response_processor.parse_resource(result, connection_id, duration_ms)

        except FHIRError as e:
            return response_processor.create_error_response(e, connection_id)

    # ==========================================================================
    # Category 4: Clinical Notes & Documents (2 tools)
    # ==========================================================================

    @mcp.tool()
    async def fhir_clinical_notes(
        connection_id: str,
        patient_id: str,
        note_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        encounter_id: str | None = None,
        _count: int = 100,
    ) -> dict[str, Any]:
        """
        Retrieve clinical notes for a patient.

        Args:
            connection_id: Which FHIR server
            patient_id: Patient reference
            note_type: Type of note (progress, discharge, history, consult, procedure, all)
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            encounter_id: Specific encounter
            _count: Maximum results

        Returns:
            Array of DocumentReference resources with content
        """
        start_time = time.time()
        try:
            params: dict[str, Any] = {
                "patient": patient_id,
                "_count": _count,
            }

            # Map note type to LOINC code
            if note_type and note_type != "all":
                loinc_code = NOTE_TYPE_LOINC.get(note_type)
                if loinc_code:
                    params["type"] = f"http://loinc.org|{loinc_code}"

            if date_from:
                params["date"] = f"ge{date_from}"
            if date_to:
                if "date" in params:
                    # FHIR allows multiple date params
                    params["date"] = [params["date"], f"le{date_to}"]
                else:
                    params["date"] = f"le{date_to}"

            if encounter_id:
                params["encounter"] = encounter_id

            result = await fhir_client.search(connection_id, "DocumentReference", params)

            duration_ms = int((time.time() - start_time) * 1000)
            return response_processor.parse_search_result(result, connection_id, duration_ms)

        except FHIRError as e:
            return response_processor.create_error_response(e, connection_id)

    @mcp.tool()
    async def fhir_document_content(
        connection_id: str,
        document_reference_id: str,
        format: str = "text",
    ) -> dict[str, Any]:
        """
        Retrieve actual document content (resolves Binary references).

        Args:
            connection_id: Which FHIR server
            document_reference_id: DocumentReference ID
            format: Output format (raw, text, base64)

        Returns:
            Document content with metadata
        """
        start_time = time.time()
        try:
            # First get the DocumentReference
            doc_ref = await fhir_client.read(
                connection_id, "DocumentReference", document_reference_id
            )

            # Extract content URL from DocumentReference
            content_list = doc_ref.get("content", [])
            if not content_list:
                return response_processor.create_error_response(
                    ValueError("No content found in DocumentReference"),
                    connection_id,
                )

            # Get the first content attachment
            attachment = content_list[0].get("attachment", {})
            content_url = attachment.get("url")
            content_type = attachment.get("contentType", "text/plain")

            result_data: dict[str, Any] = {
                "document_reference_id": document_reference_id,
                "content_type": content_type,
            }

            # If content is inline (data), decode it
            if "data" in attachment:
                import base64

                decoded = base64.b64decode(attachment["data"])
                if format == "base64":
                    result_data["content"] = attachment["data"]
                elif format == "text":
                    result_data["content"] = decoded.decode("utf-8", errors="replace")
                else:
                    result_data["content"] = decoded.decode("utf-8", errors="replace")

            # If content is a URL (Binary reference), fetch it
            elif content_url:
                # Extract Binary ID from URL
                if "/Binary/" in content_url:
                    binary_id = content_url.split("/Binary/")[-1].split("?")[0]
                    binary_resource = await fhir_client.read(connection_id, "Binary", binary_id)

                    if "data" in binary_resource:
                        import base64

                        decoded = base64.b64decode(binary_resource["data"])
                        if format == "base64":
                            result_data["content"] = binary_resource["data"]
                        else:
                            result_data["content"] = decoded.decode("utf-8", errors="replace")
                else:
                    result_data["content_url"] = content_url
                    result_data["note"] = "External URL - content not fetched"

            duration_ms = int((time.time() - start_time) * 1000)
            return response_processor.create_success_response(
                data=result_data,
                connection_id=connection_id,
                duration_ms=duration_ms,
            )

        except FHIRError as e:
            return response_processor.create_error_response(e, connection_id)

    # ==========================================================================
    # Category 5: Bulk Data Export (4 tools)
    # ==========================================================================

    @mcp.tool()
    async def fhir_bulk_export_start(
        connection_id: str,
        export_type: str,
        group_id: str | None = None,
        _type: list[str] | None = None,
        _since: str | None = None,
        _typeFilter: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Initiate FHIR Bulk Data export.

        Args:
            connection_id: Which FHIR server
            export_type: Export type (system, patient, group)
            group_id: Required for group export
            _type: Resource types to export
            _since: Only resources modified since (ISO datetime)
            _typeFilter: FHIR search filters per type

        Returns:
            Export job ID and polling URL
        """
        start_time = time.time()
        try:
            # Build export path
            if export_type == "system":
                path = "$export"
            elif export_type == "patient":
                path = "Patient/$export"
            elif export_type == "group":
                if not group_id:
                    return response_processor.create_error_response(
                        ValueError("group_id required for group export"),
                        connection_id,
                    )
                path = f"Group/{group_id}/$export"
            else:
                return response_processor.create_error_response(
                    ValueError(f"Invalid export_type: {export_type}"),
                    connection_id,
                )

            params: dict[str, Any] = {}
            if _type:
                params["_type"] = ",".join(_type)
            if _since:
                params["_since"] = _since
            if _typeFilter:
                params["_typeFilter"] = _typeFilter

            # Make the export request
            # Note: Bulk export returns 202 Accepted with Content-Location header
            connection = await connection_manager.ensure_authenticated(connection_id)

            import httpx

            headers = {
                "Accept": "application/fhir+json",
                "Prefer": "respond-async",
            }
            if connection.auth_result:
                headers["Authorization"] = connection.auth_result.authorization_header

            url = f"{connection.base_url}/{path}"
            if params:
                from urllib.parse import urlencode

                url = f"{url}?{urlencode(params, doseq=True)}"

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 202:
                    # Success - extract job info from headers
                    content_location = response.headers.get("Content-Location", "")
                    job_id = content_location.split("/")[-1] if content_location else None

                    result_data = {
                        "job_id": job_id,
                        "status": "pending",
                        "polling_url": content_location,
                        "export_type": export_type,
                    }
                    if group_id:
                        result_data["group_id"] = group_id

                    duration_ms = int((time.time() - start_time) * 1000)
                    return response_processor.create_success_response(
                        data=result_data,
                        connection_id=connection_id,
                        duration_ms=duration_ms,
                    )
                else:
                    return response_processor.create_error_response(
                        Exception(f"Bulk export failed: {response.status_code} - {response.text}"),
                        connection_id,
                    )

        except FHIRError as e:
            return response_processor.create_error_response(e, connection_id)

    @mcp.tool()
    async def fhir_bulk_export_status(
        connection_id: str,
        job_id: str,
    ) -> dict[str, Any]:
        """
        Check bulk export job status.

        Args:
            connection_id: Which FHIR server
            job_id: Export job ID

        Returns:
            Status (pending, in-progress, complete, error), progress %, file list if complete
        """
        start_time = time.time()
        try:
            connection = await connection_manager.ensure_authenticated(connection_id)

            import httpx

            headers = {
                "Accept": "application/fhir+json",
            }
            if connection.auth_result:
                headers["Authorization"] = connection.auth_result.authorization_header

            # Construct status URL - may need vendor-specific handling
            status_url = f"{connection.base_url}/$export-status/{job_id}"

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(status_url, headers=headers)

                result_data: dict[str, Any] = {"job_id": job_id}

                if response.status_code == 202:
                    # Still in progress
                    result_data["status"] = "in-progress"
                    # Try to get progress from headers
                    progress = response.headers.get("X-Progress")
                    if progress:
                        result_data["progress"] = progress

                elif response.status_code == 200:
                    # Complete
                    result_data["status"] = "complete"
                    export_result = response.json()

                    # Extract file information
                    files = []
                    for output in export_result.get("output", []):
                        files.append(
                            {
                                "type": output.get("type"),
                                "url": output.get("url"),
                                "count": output.get("count"),
                            }
                        )
                    result_data["files"] = files
                    result_data["transaction_time"] = export_result.get("transactionTime")

                else:
                    result_data["status"] = "error"
                    result_data["error"] = response.text

                duration_ms = int((time.time() - start_time) * 1000)
                return response_processor.create_success_response(
                    data=result_data,
                    connection_id=connection_id,
                    duration_ms=duration_ms,
                )

        except FHIRError as e:
            return response_processor.create_error_response(e, connection_id)

    @mcp.tool()
    async def fhir_bulk_export_download(
        connection_id: str,
        job_id: str,
        resource_type: str | None = None,
        file_index: int | None = None,
        streaming: bool = False,
    ) -> dict[str, Any]:
        """
        Download completed bulk export files.

        Args:
            connection_id: Which FHIR server
            job_id: Export job ID
            resource_type: Download specific type only
            file_index: Specific file index
            streaming: Stream large files (default false)

        Returns:
            NDJSON content or stream reference
        """
        start_time = time.time()
        try:
            # First get the export status to get file URLs
            status_result = await fhir_bulk_export_status(connection_id, job_id)

            if not status_result.get("success"):
                return status_result

            status_data = status_result.get("data", {})
            if status_data.get("status") != "complete":
                return response_processor.create_error_response(
                    Exception(f"Export not complete: {status_data.get('status')}"),
                    connection_id,
                )

            files = status_data.get("files", [])

            # Filter by resource type if specified
            if resource_type:
                files = [f for f in files if f.get("type") == resource_type]

            # Filter by file index if specified
            if file_index is not None:
                if file_index < len(files):
                    files = [files[file_index]]
                else:
                    return response_processor.create_error_response(
                        ValueError(f"File index {file_index} out of range"),
                        connection_id,
                    )

            # Download files
            connection = await connection_manager.ensure_authenticated(connection_id)

            import httpx

            headers = {}
            if connection.auth_result:
                headers["Authorization"] = connection.auth_result.authorization_header

            downloaded_data: list[dict[str, Any]] = []

            async with httpx.AsyncClient(timeout=300.0) as client:
                for file_info in files:
                    file_url = file_info.get("url")
                    if not file_url:
                        continue

                    response = await client.get(file_url, headers=headers)
                    if response.status_code == 200:
                        # Parse NDJSON
                        import json

                        lines = response.text.strip().split("\n")
                        resources = [json.loads(line) for line in lines if line.strip()]

                        downloaded_data.append(
                            {
                                "type": file_info.get("type"),
                                "count": len(resources),
                                "resources": resources,
                            }
                        )

            duration_ms = int((time.time() - start_time) * 1000)
            return response_processor.create_success_response(
                data={"job_id": job_id, "files": downloaded_data},
                connection_id=connection_id,
                duration_ms=duration_ms,
            )

        except FHIRError as e:
            return response_processor.create_error_response(e, connection_id)

    @mcp.tool()
    async def fhir_bulk_export_cancel(
        connection_id: str,
        job_id: str,
    ) -> dict[str, Any]:
        """
        Cancel a running bulk export.

        Args:
            connection_id: Which FHIR server
            job_id: Export job ID

        Returns:
            Cancellation status
        """
        start_time = time.time()
        try:
            connection = await connection_manager.ensure_authenticated(connection_id)

            import httpx

            headers = {}
            if connection.auth_result:
                headers["Authorization"] = connection.auth_result.authorization_header

            cancel_url = f"{connection.base_url}/$export-status/{job_id}"

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.delete(cancel_url, headers=headers)

                result_data = {
                    "job_id": job_id,
                    "cancelled": response.status_code in (200, 202, 204),
                }

                duration_ms = int((time.time() - start_time) * 1000)
                return response_processor.create_success_response(
                    data=result_data,
                    connection_id=connection_id,
                    duration_ms=duration_ms,
                )

        except FHIRError as e:
            return response_processor.create_error_response(e, connection_id)

    # ==========================================================================
    # Category 6: Group Management (4 tools)
    # ==========================================================================

    @mcp.tool()
    async def fhir_group_create(
        connection_id: str,
        name: str,
        patient_ids: list[str],
        description: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a patient group for bulk export.

        Args:
            connection_id: Which FHIR server
            name: Group name
            patient_ids: Array of patient IDs
            description: Group description

        Returns:
            Created Group resource with ID
        """
        start_time = time.time()
        try:
            # Build Group resource
            group_resource: dict[str, Any] = {
                "resourceType": "Group",
                "type": "person",
                "actual": True,
                "name": name,
                "member": [{"entity": {"reference": f"Patient/{pid}"}} for pid in patient_ids],
            }

            if description:
                group_resource["text"] = {
                    "status": "generated",
                    "div": f"<div>{description}</div>",
                }

            result = await fhir_client.post(connection_id, "Group", group_resource)

            duration_ms = int((time.time() - start_time) * 1000)
            return response_processor.parse_resource(result, connection_id, duration_ms)

        except FHIRError as e:
            return response_processor.create_error_response(e, connection_id)

    @mcp.tool()
    async def fhir_group_list(
        connection_id: str,
    ) -> dict[str, Any]:
        """
        List available patient groups.

        Args:
            connection_id: Which FHIR server

        Returns:
            Array of Group resources
        """
        start_time = time.time()
        try:
            params = {"type": "person", "_count": 100}
            result = await fhir_client.search(connection_id, "Group", params)

            duration_ms = int((time.time() - start_time) * 1000)
            return response_processor.parse_search_result(result, connection_id, duration_ms)

        except FHIRError as e:
            return response_processor.create_error_response(e, connection_id)

    @mcp.tool()
    async def fhir_group_members(
        connection_id: str,
        group_id: str,
    ) -> dict[str, Any]:
        """
        Get members of a group.

        Args:
            connection_id: Which FHIR server
            group_id: Group ID

        Returns:
            Array of patient references
        """
        start_time = time.time()
        try:
            result = await fhir_client.read(connection_id, "Group", group_id)

            # Extract member references
            members = result.get("member", [])
            patient_refs = []
            for member in members:
                entity = member.get("entity", {})
                ref = entity.get("reference", "")
                if ref.startswith("Patient/"):
                    patient_refs.append(ref.replace("Patient/", ""))

            duration_ms = int((time.time() - start_time) * 1000)
            return response_processor.create_success_response(
                data={
                    "group_id": group_id,
                    "member_count": len(patient_refs),
                    "patient_ids": patient_refs,
                },
                connection_id=connection_id,
                duration_ms=duration_ms,
            )

        except FHIRError as e:
            return response_processor.create_error_response(e, connection_id)

    @mcp.tool()
    async def fhir_group_update(
        connection_id: str,
        group_id: str,
        add_patients: list[str] | None = None,
        remove_patients: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Add/remove patients from a group.

        Args:
            connection_id: Which FHIR server
            group_id: Group ID
            add_patients: Patient IDs to add
            remove_patients: Patient IDs to remove

        Returns:
            Updated Group resource
        """
        start_time = time.time()
        try:
            # Get current group
            group = await fhir_client.read(connection_id, "Group", group_id)

            # Get current members
            members = group.get("member", [])
            current_ids = set()
            for member in members:
                ref = member.get("entity", {}).get("reference", "")
                if ref.startswith("Patient/"):
                    current_ids.add(ref.replace("Patient/", ""))

            # Apply changes
            if remove_patients:
                current_ids -= set(remove_patients)
            if add_patients:
                current_ids |= set(add_patients)

            # Update group
            group["member"] = [
                {"entity": {"reference": f"Patient/{pid}"}} for pid in current_ids
            ]

            result = await fhir_client.put(connection_id, f"Group/{group_id}", group)

            duration_ms = int((time.time() - start_time) * 1000)
            return response_processor.parse_resource(result, connection_id, duration_ms)

        except FHIRError as e:
            return response_processor.create_error_response(e, connection_id)

    # ==========================================================================
    # Category 7: Metadata & Capabilities (2 tools)
    # ==========================================================================

    @mcp.tool()
    async def fhir_capability_statement(
        connection_id: str,
    ) -> dict[str, Any]:
        """
        Get server's CapabilityStatement (what it supports).

        Args:
            connection_id: Which FHIR server

        Returns:
            CapabilityStatement resource
        """
        start_time = time.time()
        try:
            result = await fhir_client.get(connection_id, "metadata")

            duration_ms = int((time.time() - start_time) * 1000)
            return response_processor.parse_resource(result, connection_id, duration_ms)

        except FHIRError as e:
            return response_processor.create_error_response(e, connection_id)

    @mcp.tool()
    async def fhir_supported_resources(
        connection_id: str,
    ) -> dict[str, Any]:
        """
        Get simplified list of supported resources.

        Args:
            connection_id: Which FHIR server

        Returns:
            Array of resource types with search parameters
        """
        start_time = time.time()
        try:
            capability = await fhir_client.get(connection_id, "metadata")

            # Extract resource information
            resources = []
            rest = capability.get("rest", [])
            for rest_entry in rest:
                if rest_entry.get("mode") == "server":
                    for resource in rest_entry.get("resource", []):
                        resource_info = {
                            "type": resource.get("type"),
                            "profile": resource.get("profile"),
                            "interactions": [
                                i.get("code") for i in resource.get("interaction", [])
                            ],
                            "search_params": [
                                sp.get("name") for sp in resource.get("searchParam", [])
                            ],
                        }
                        resources.append(resource_info)

            duration_ms = int((time.time() - start_time) * 1000)
            return response_processor.create_success_response(
                data={"resources": resources, "count": len(resources)},
                connection_id=connection_id,
                duration_ms=duration_ms,
            )

        except FHIRError as e:
            return response_processor.create_error_response(e, connection_id)

    return mcp
