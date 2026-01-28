"""CDS Hooks service discovery and invocation.

This module provides functionality to discover and invoke
CDS Hooks services from FHIR servers.

See: https://cds-hooks.hl7.org/2.0/
"""

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin

import httpx

from fhir_r4_mcp.cds.hooks import (
    CDSHook,
    CDSHookRequest,
    CDSHookResponse,
    HookType,
)
from fhir_r4_mcp.core.connection_manager import connection_manager
from fhir_r4_mcp.utils.errors import FHIRError
from fhir_r4_mcp.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CDSServiceDiscovery:
    """CDS Hooks service discovery response."""

    services: list[CDSHook] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CDSServiceDiscovery":
        """Parse from CDS Hooks discovery response."""
        services = []
        for service_data in data.get("services", []):
            try:
                hook_type = HookType(service_data.get("hook", ""))
            except ValueError:
                # Unknown hook type, skip
                logger.warning(f"Unknown hook type: {service_data.get('hook')}")
                continue

            services.append(
                CDSHook(
                    id=service_data.get("id", ""),
                    hook=hook_type,
                    title=service_data.get("title", ""),
                    description=service_data.get("description", ""),
                    prefetch=service_data.get("prefetch", {}),
                    usage_requirements=service_data.get("usageRequirements"),
                )
            )

        return cls(services=services)

    def get_service(self, service_id: str) -> CDSHook | None:
        """Get a service by ID."""
        for service in self.services:
            if service.id == service_id:
                return service
        return None

    def get_services_by_hook(self, hook_type: HookType) -> list[CDSHook]:
        """Get all services for a hook type."""
        return [s for s in self.services if s.hook == hook_type]


class CDSService:
    """CDS Hooks service client.

    Provides methods to discover CDS services and invoke hooks.
    """

    def __init__(
        self,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the CDS service client.

        Args:
            timeout: Request timeout in seconds
        """
        self._timeout = timeout
        self._discovered: dict[str, CDSServiceDiscovery] = {}

    def _get_cds_base_url(self, fhir_base_url: str) -> str:
        """Get CDS Hooks base URL from FHIR base URL.

        CDS services are typically at the same base URL with /cds-services path.
        """
        # Remove trailing slash and add cds-services
        base = fhir_base_url.rstrip("/")
        return f"{base}/cds-services"

    async def _get_headers(self, connection_id: str) -> dict[str, str]:
        """Get request headers including authorization."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        try:
            connection = await connection_manager.ensure_authenticated(connection_id)
            if connection.auth_result:
                headers["Authorization"] = connection.auth_result.authorization_header
        except Exception:
            pass

        return headers

    async def discover_services(
        self,
        connection_id: str,
        cds_url: str | None = None,
    ) -> CDSServiceDiscovery:
        """Discover available CDS Hooks services.

        Args:
            connection_id: FHIR connection ID
            cds_url: Optional CDS service URL (derived from FHIR URL if not provided)

        Returns:
            CDSServiceDiscovery with available services
        """
        try:
            connection = await connection_manager.get_connection(connection_id)
            if not connection:
                raise FHIRError(f"Connection not found: {connection_id}")

            # Determine CDS URL
            if cds_url:
                discovery_url = cds_url.rstrip("/")
            else:
                discovery_url = self._get_cds_base_url(connection.base_url)

            headers = await self._get_headers(connection_id)

            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(discovery_url, headers=headers)

                if response.status_code == 404:
                    logger.info(f"No CDS services available at {discovery_url}")
                    return CDSServiceDiscovery()

                if not response.is_success:
                    raise FHIRError(
                        f"CDS discovery failed: {response.status_code} - {response.text}"
                    )

                data = response.json()
                discovery = CDSServiceDiscovery.from_dict(data)

                # Cache discovery
                self._discovered[connection_id] = discovery

                logger.info(
                    f"Discovered {len(discovery.services)} CDS services for {connection_id}"
                )

                return discovery

        except FHIRError:
            raise
        except Exception as e:
            logger.error(f"CDS discovery error: {e}")
            raise FHIRError(f"CDS discovery failed: {e}")

    async def invoke_hook(
        self,
        connection_id: str,
        hook: str,
        context: dict[str, Any],
        prefetch: dict[str, Any] | None = None,
        cds_url: str | None = None,
        service_id: str | None = None,
    ) -> CDSHookResponse:
        """Invoke a CDS Hook.

        Args:
            connection_id: FHIR connection ID
            hook: Hook type to invoke (e.g., "patient-view")
            context: Hook-specific context data
            prefetch: Pre-fetched FHIR resources
            cds_url: Optional CDS service URL
            service_id: Optional specific service ID to invoke

        Returns:
            CDSHookResponse with cards
        """
        import uuid

        try:
            connection = await connection_manager.get_connection(connection_id)
            if not connection:
                raise FHIRError(f"Connection not found: {connection_id}")

            # Determine CDS URL
            if cds_url:
                base_url = cds_url.rstrip("/")
            else:
                base_url = self._get_cds_base_url(connection.base_url)

            # Build service URL
            if service_id:
                service_url = f"{base_url}/{service_id}"
            else:
                # Use hook type as service ID
                service_url = f"{base_url}/{hook}"

            # Build request
            request = CDSHookRequest(
                hook=hook,
                hook_instance=str(uuid.uuid4()),
                context=context,
                prefetch=prefetch or {},
                fhir_server=connection.base_url,
            )

            # Add FHIR authorization if available
            if connection.auth_result:
                request.fhir_authorization = {
                    "access_token": connection.auth_result.access_token,
                    "token_type": "Bearer",
                    "scope": connection.auth_result.scope or "",
                }

            headers = await self._get_headers(connection_id)

            request_body = {
                "hook": request.hook,
                "hookInstance": request.hook_instance,
                "context": request.context,
                "prefetch": request.prefetch,
            }
            if request.fhir_server:
                request_body["fhirServer"] = request.fhir_server
            if request.fhir_authorization:
                request_body["fhirAuthorization"] = request.fhir_authorization

            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    service_url,
                    json=request_body,
                    headers=headers,
                )

                if not response.is_success:
                    raise FHIRError(
                        f"CDS hook invocation failed: {response.status_code} - {response.text}"
                    )

                data = response.json()

                # Parse response
                cds_response = CDSHookResponse()

                from fhir_r4_mcp.cds.hooks import (
                    CDSAction,
                    CDSCard,
                    CDSLink,
                    CDSSuggestion,
                    CardIndicator,
                    SelectionBehavior,
                )

                for card_data in data.get("cards", []):
                    try:
                        indicator = CardIndicator(card_data.get("indicator", "info"))
                    except ValueError:
                        indicator = CardIndicator.INFO

                    card = CDSCard(
                        summary=card_data.get("summary", ""),
                        indicator=indicator,
                        source=card_data.get("source", {"label": "CDS Service"}),
                        detail=card_data.get("detail"),
                    )

                    # Parse suggestions
                    for sug_data in card_data.get("suggestions", []):
                        suggestion = CDSSuggestion(
                            label=sug_data.get("label", ""),
                            uuid=sug_data.get("uuid"),
                            is_recommended=sug_data.get("isRecommended", False),
                        )

                        for action_data in sug_data.get("actions", []):
                            suggestion.actions.append(
                                CDSAction(
                                    type=action_data.get("type", ""),
                                    description=action_data.get("description", ""),
                                    resource=action_data.get("resource"),
                                    resource_id=action_data.get("resourceId"),
                                )
                            )

                        card.suggestions.append(suggestion)

                    # Parse links
                    for link_data in card_data.get("links", []):
                        card.links.append(
                            CDSLink(
                                label=link_data.get("label", ""),
                                url=link_data.get("url", ""),
                                type=link_data.get("type", "absolute"),
                                app_context=link_data.get("appContext"),
                            )
                        )

                    # Parse selection behavior
                    if "selectionBehavior" in card_data:
                        try:
                            card.selection_behavior = SelectionBehavior(
                                card_data["selectionBehavior"]
                            )
                        except ValueError:
                            pass

                    card.override_reasons = card_data.get("overrideReasons")

                    cds_response.cards.append(card)

                # Parse system actions
                for action_data in data.get("systemActions", []):
                    cds_response.system_actions.append(
                        CDSAction(
                            type=action_data.get("type", ""),
                            description=action_data.get("description", ""),
                            resource=action_data.get("resource"),
                            resource_id=action_data.get("resourceId"),
                        )
                    )

                logger.info(
                    f"CDS hook {hook} returned {len(cds_response.cards)} cards"
                )

                return cds_response

        except FHIRError:
            raise
        except Exception as e:
            logger.error(f"CDS hook invocation error: {e}")
            raise FHIRError(f"CDS hook invocation failed: {e}")

    def get_cached_discovery(
        self,
        connection_id: str,
    ) -> CDSServiceDiscovery | None:
        """Get cached service discovery for a connection."""
        return self._discovered.get(connection_id)

    def clear_cache(self, connection_id: str | None = None) -> None:
        """Clear discovery cache.

        Args:
            connection_id: Clear specific connection, or all if None
        """
        if connection_id:
            self._discovered.pop(connection_id, None)
        else:
            self._discovered.clear()


# Global CDS service instance
cds_service = CDSService()
