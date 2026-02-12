"""Unified data models for OSINT results."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class GeoLocation(BaseModel):
    """Geographic location data."""

    country: str | None = None
    country_code: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    asn: str | None = None
    org: str | None = None


class PortInfo(BaseModel):
    """Information about an open port."""

    port: int
    protocol: str = "tcp"
    service: str | None = None
    product: str | None = None
    version: str | None = None
    banner: str | None = None


class Vulnerability(BaseModel):
    """CVE vulnerability information."""

    cve_id: str
    cvss: float | None = None
    summary: str | None = None
    references: list[str] = Field(default_factory=list)


class IPReport(BaseModel):
    """Unified IP address intelligence report."""

    ip: str
    provider: str
    hostnames: list[str] = Field(default_factory=list)
    ports: list[PortInfo] = Field(default_factory=list)
    vulns: list[Vulnerability] = Field(default_factory=list)
    geo: GeoLocation | None = None
    os: str | None = None
    reputation_score: float | None = None
    tags: list[str] = Field(default_factory=list)
    last_seen: datetime | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class EmailContact(BaseModel):
    """An email contact found for a domain."""

    email: str
    first_name: str | None = None
    last_name: str | None = None
    position: str | None = None
    department: str | None = None
    confidence: int | None = None
    sources: list[str] = Field(default_factory=list)


class DomainReport(BaseModel):
    """Unified domain intelligence report."""

    domain: str
    provider: str
    organization: str | None = None
    emails: list[EmailContact] = Field(default_factory=list)
    subdomains: list[str] = Field(default_factory=list)
    dns_records: dict[str, list[str]] = Field(default_factory=dict)
    technologies: list[str] = Field(default_factory=list)
    reputation_score: float | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class EmailReport(BaseModel):
    """Unified email intelligence report."""

    email: str
    provider: str
    deliverable: bool | None = None
    disposable: bool | None = None
    first_name: str | None = None
    last_name: str | None = None
    organization: str | None = None
    sources: list[str] = Field(default_factory=list)
    confidence: int | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class URLReport(BaseModel):
    """Unified URL intelligence report."""

    url: str
    provider: str
    malicious: bool | None = None
    categories: list[str] = Field(default_factory=list)
    reputation_score: float | None = None
    screenshot_url: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


ReportType = IPReport | DomainReport | EmailReport | URLReport


class AggregatedReport(BaseModel):
    """Combined results from multiple providers."""

    query: str
    query_type: str
    reports: list[ReportType] = Field(default_factory=list)
    confidence: float = 0.0
    providers_queried: list[str] = Field(default_factory=list)
    providers_failed: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    def merge_confidence(self) -> float:
        """Calculate overall confidence from provider results."""
        if not self.reports:
            return 0.0
        scores = []
        for r in self.reports:
            if hasattr(r, "reputation_score") and r.reputation_score is not None:
                scores.append(r.reputation_score)
            elif hasattr(r, "confidence") and r.confidence is not None:
                scores.append(r.confidence / 100.0)
        if not scores:
            return 0.5
        return sum(scores) / len(scores)
