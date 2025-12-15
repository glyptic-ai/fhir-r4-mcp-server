"""Vendor-specific profiles for EHR systems."""

from fhir_r4_mcp.vendors.base import VendorProfile
from fhir_r4_mcp.vendors.generic import GenericProfile
from fhir_r4_mcp.vendors.nextgen import NextGenProfile

__all__ = ["VendorProfile", "GenericProfile", "NextGenProfile"]
