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

    # Extended personal identifiers
    aliases: list[str] = Field(default_factory=list)
    date_of_birth: str | None = None  # YYYY-MM-DD
    age_range: str | None = None  # e.g. "30-40"
    location: str | None = None  # City, State, Country
    address: str | None = None  # Full street address
    nationality: str | None = None
    gender: str | None = None
    employer: str | None = None  # Current workplace
    occupation: str | None = None
    education: str | None = None  # School/university
    social_media: dict[str, str] = Field(default_factory=dict)  # platform -> handle/url
    vehicle: str | None = None  # Vehicle description / plate
    physical_description: str | None = None  # Height, weight, hair, eyes, etc.
    notes: str | None = None  # Free-form investigator notes
    photo_ids: list[str] = Field(default_factory=list)  # References to uploaded photos


class InvestigationCreateRequest(InvestigateRequest):
    """Investigation creation request with optional case name."""

    investigation_name: str | None = None


class InvestigationSummary(BaseModel):
    """Summary of an investigation for list views."""

    id: str
    name: str | None = None
    subject_name: str | None = None
    status: str
    created_at: str
    updated_at: str
    has_results: bool


class InvestigationFull(BaseModel):
    """Full investigation with all fields, results, and timeline."""

    id: str
    name: str | None = None
    status: str
    created_at: str
    updated_at: str
    subject_name: str | None = None
    aliases: list[str] = []
    date_of_birth: str | None = None
    age_range: str | None = None
    email: str | None = None
    phone: str | None = None
    ip: str | None = None
    domain: str | None = None
    company: str | None = None
    employer: str | None = None
    occupation: str | None = None
    education: str | None = None
    location: str | None = None
    address: str | None = None
    nationality: str | None = None
    gender: str | None = None
    social_media: dict[str, str] = {}
    vehicle: str | None = None
    physical_description: str | None = None
    notes: str | None = None
    photo_ids: list[str] = []
    results: dict | None = None
    timeline: list[dict] = []


class TimelineEvent(BaseModel):
    """A single event on an investigation timeline."""

    id: str
    timestamp: str
    event_type: str
    description: str | None = None
    data: dict | None = None


class AddNoteRequest(BaseModel):
    """Request body for adding a note."""

    note: str


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
    aliases: list[str] = Field(default_factory=list)
    date_of_birth: str | None = None
    age_range: str | None = None
    location: str | None = None
    address: str | None = None
    nationality: str | None = None
    gender: str | None = None
    employer: str | None = None
    occupation: str | None = None
    education: str | None = None
    physical_description: str | None = None
    vehicle: str | None = None
    notes: str | None = None
    photo_ids: list[str] = Field(default_factory=list)
    emails: list[str] = Field(default_factory=list)
    phones: list[str] = Field(default_factory=list)
    ips: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    companies: list[str] = Field(default_factory=list)


class DigitalFootprint(BaseModel):
    """Digital footprint data."""

    sources: list[str] = Field(default_factory=list)
    urls: list[dict[str, Any]] = Field(default_factory=list)
    social_media: dict[str, str] = Field(default_factory=dict)  # platform -> handle/url


class RelationshipEdge(BaseModel):
    """A relationship between two entities."""

    source: str
    target: str
    relationship: str
    source_type: str = "entity"
    target_type: str = "entity"


class SocialPresenceProfile(BaseModel):
    """A social media profile found during username enumeration."""

    platform: str
    url: str
    username: str
    exists: bool = True
    category: str | None = None
    provider: str = ""  # "sherlock" or "maigret"


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
    social_presence: list[SocialPresenceProfile] = Field(default_factory=list)
    registered_services: list[str] = Field(default_factory=list)
    relationships: list[RelationshipEdge] = Field(default_factory=list)
    providers_queried: list[str] = Field(default_factory=list)
    providers_failed: list[str] = Field(default_factory=list)
    query_count: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
