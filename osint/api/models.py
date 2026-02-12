"""Pydantic request/response models for the API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Request Models ──────────────────────────────────────────────


class LookupRequest(BaseModel):
    """Single-query lookup request."""

    query: str
    query_type: str | None = None  # auto-detected if omitted


class InvestigateRequest(BaseModel):
    """Multi-field person investigation request."""

    name: str | None = None
    email: str | None = None
    phone: str | None = None
    ip: str | None = None
    domain: str | None = None
    company: str | None = None


# ── Response Models ─────────────────────────────────────────────


class ProviderInfo(BaseModel):
    """Provider status information."""

    name: str
    available: bool
    supported_types: list[str]
    rate_limit: dict[str, Any] = Field(default_factory=dict)


class ProvidersResponse(BaseModel):
    """List of all providers and their status."""

    providers: list[ProviderInfo]
    total: int
    available: int


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    version: str = "0.1.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    providers_available: int = 0


class LookupResponse(BaseModel):
    """Response for a single lookup."""

    query: str
    query_type: str
    reports: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.0
    providers_queried: list[str] = Field(default_factory=list)
    providers_failed: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ThreatInfo(BaseModel):
    """Threat assessment data."""

    score: float = 0.0  # 0-100
    level: str = "unknown"  # low, medium, high, critical
    abuse_reports: list[dict[str, Any]] = Field(default_factory=list)
    malware_detected: bool = False
    phishing_detected: bool = False
    vulnerabilities: list[dict[str, Any]] = Field(default_factory=list)
    indicators: list[str] = Field(default_factory=list)


class GeoInfo(BaseModel):
    """Geographic information."""

    locations: list[dict[str, Any]] = Field(default_factory=list)


class NetworkInfo(BaseModel):
    """Network intelligence data."""

    ips: list[dict[str, Any]] = Field(default_factory=list)
    ports: list[dict[str, Any]] = Field(default_factory=list)
    services: list[dict[str, Any]] = Field(default_factory=list)
    hostnames: list[str] = Field(default_factory=list)


class EmailInfo(BaseModel):
    """Email intelligence data."""

    emails: list[dict[str, Any]] = Field(default_factory=list)
    verified: list[dict[str, Any]] = Field(default_factory=list)


class PhoneInfo(BaseModel):
    """Phone intelligence data."""

    numbers: list[dict[str, Any]] = Field(default_factory=list)


class DomainInfo(BaseModel):
    """Domain intelligence data."""

    domains: list[dict[str, Any]] = Field(default_factory=list)
    dns_records: dict[str, list[str]] = Field(default_factory=dict)
    subdomains: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)


class OrganizationInfo(BaseModel):
    """Organization intelligence data."""

    companies: list[dict[str, Any]] = Field(default_factory=list)


class IdentityInfo(BaseModel):
    """Identity summary data."""

    name: str | None = None
    emails: list[str] = Field(default_factory=list)
    phones: list[str] = Field(default_factory=list)
    ips: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    companies: list[str] = Field(default_factory=list)


class DigitalFootprint(BaseModel):
    """Digital footprint data."""

    sources: list[str] = Field(default_factory=list)
    urls: list[dict[str, Any]] = Field(default_factory=list)


class RelationshipEdge(BaseModel):
    """A relationship between two entities."""

    source: str
    target: str
    relationship: str
    source_type: str = "entity"
    target_type: str = "entity"


class InvestigateResponse(BaseModel):
    """Full investigation response with cross-referenced data."""

    identity: IdentityInfo = Field(default_factory=IdentityInfo)
    network: NetworkInfo = Field(default_factory=NetworkInfo)
    threats: ThreatInfo = Field(default_factory=ThreatInfo)
    geo: GeoInfo = Field(default_factory=GeoInfo)
    email_intel: EmailInfo = Field(default_factory=EmailInfo)
    phone_intel: PhoneInfo = Field(default_factory=PhoneInfo)
    domain_intel: DomainInfo = Field(default_factory=DomainInfo)
    organization: OrganizationInfo = Field(default_factory=OrganizationInfo)
    digital_footprint: DigitalFootprint = Field(default_factory=DigitalFootprint)
    relationships: list[RelationshipEdge] = Field(default_factory=list)
    providers_queried: list[str] = Field(default_factory=list)
    providers_failed: list[str] = Field(default_factory=list)
    query_count: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
