"""Investigation endpoint — full person/entity investigation with cross-referencing."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from osint.aggregator import aggregate
from osint.api.models import (
    DigitalFootprint,
    DomainInfo,
    EmailInfo,
    GeoInfo,
    IdentityInfo,
    InvestigateRequest,
    InvestigateResponse,
    NetworkInfo,
    OrganizationInfo,
    PhoneInfo,
    RelationshipEdge,
    ThreatInfo,
)
from osint.core.models import (
    AggregatedReport,
    DomainReport,
    EmailReport,
    IPReport,
    URLReport,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _extract_domain_from_email(email: str) -> str | None:
    """Extract domain from email address."""
    if "@" in email:
        return email.split("@")[-1]
    return None


async def _run_query(query: str, query_type: str) -> AggregatedReport:
    """Run a single aggregated query, catching errors."""
    try:
        return await aggregate(query=query, query_type=query_type)
    except Exception as e:
        logger.error("Investigation query failed: %s (%s): %s", query, query_type, e)
        return AggregatedReport(
            query=query,
            query_type=query_type,
            providers_queried=[],
            providers_failed=[f"error: {e}"],
        )


@router.post("/investigate", response_model=InvestigateResponse)
async def investigate(req: InvestigateRequest) -> InvestigateResponse:
    """Run a full investigation across all provided identifiers.

    1. Fan out queries for each provided field concurrently
    2. Cross-reference results (email → domain, domain → emails, etc.)
    3. Build unified response with categorized intelligence
    """
    # Validate at least one field is provided
    fields = {
        "email": req.email,
        "phone": req.phone,
        "ip": req.ip,
        "domain": req.domain,
        "company": req.company,
    }
    active_fields = {k: v for k, v in fields.items() if v}

    if not active_fields and not req.name:
        raise HTTPException(
            status_code=400,
            detail="At least one identifier (name, email, phone, ip, domain, company) is required",
        )

    # Phase 1: Run initial queries concurrently
    initial_tasks: list[tuple[str, str, str]] = []  # (query, query_type, field_name)

    if req.email:
        initial_tasks.append((req.email.strip(), "email", "email"))
        # Also derive domain from email
        domain = _extract_domain_from_email(req.email.strip())
        if domain and domain != req.domain:
            initial_tasks.append((domain, "domain", "email_domain"))

    if req.domain:
        initial_tasks.append((req.domain.strip(), "domain", "domain"))

    if req.ip:
        initial_tasks.append((req.ip.strip(), "ip", "ip"))

    if req.phone:
        initial_tasks.append((req.phone.strip(), "phone", "phone"))

    if req.company:
        initial_tasks.append((req.company.strip(), "company", "company"))

    # Use employer as company search if company not provided
    if req.employer and not req.company:
        initial_tasks.append((req.employer.strip(), "company", "employer"))

    # Fan out all initial queries concurrently
    coros = [_run_query(q, qt) for q, qt, _ in initial_tasks]
    results: list[AggregatedReport] = await asyncio.gather(*coros)

    # Phase 2: Cross-reference — discover new entities from results
    discovered_domains: set[str] = set()
    discovered_ips: set[str] = set()
    discovered_emails: set[str] = set()

    for report in results:
        for r in report.reports:
            if isinstance(r, DomainReport):
                for email_contact in r.emails:
                    if email_contact.email:
                        discovered_emails.add(email_contact.email)
                for sub in r.subdomains:
                    discovered_domains.add(sub)
            elif isinstance(r, IPReport):
                for hostname in r.hostnames:
                    discovered_domains.add(hostname)
            elif isinstance(r, EmailReport):
                if r.organization:
                    pass  # Could discover more

    # Phase 2b: Run cross-reference queries for newly discovered IPs from DNS
    cross_ref_tasks: list[tuple[str, str, str]] = []
    already_queried = {q for q, _, _ in initial_tasks}

    for ip in discovered_ips:
        if ip not in already_queried:
            cross_ref_tasks.append((ip, "ip", "crossref_ip"))

    # Limit cross-reference to avoid explosion
    cross_ref_tasks = cross_ref_tasks[:5]

    if cross_ref_tasks:
        cross_coros = [_run_query(q, qt) for q, qt, _ in cross_ref_tasks]
        cross_results = await asyncio.gather(*cross_coros)
        results.extend(cross_results)

    # Phase 3: Build unified response
    response = _build_response(req, results, initial_tasks + cross_ref_tasks)
    return response


def _build_response(
    req: InvestigateRequest,
    results: list[AggregatedReport],
    tasks: list[tuple[str, str, str]],
) -> InvestigateResponse:
    """Build the unified investigation response from all results."""
    identity = IdentityInfo(
        name=req.name,
        aliases=req.aliases,
        date_of_birth=req.date_of_birth,
        age_range=req.age_range,
        location=req.location,
        address=req.address,
        nationality=req.nationality,
        gender=req.gender,
        employer=req.employer,
        occupation=req.occupation,
        education=req.education,
        physical_description=req.physical_description,
        vehicle=req.vehicle,
        notes=req.notes,
        photo_ids=req.photo_ids,
    )
    network = NetworkInfo()
    threats = ThreatInfo()
    geo = GeoInfo()
    email_intel = EmailInfo()
    phone_intel = PhoneInfo()
    domain_intel = DomainInfo()
    org_info = OrganizationInfo()
    footprint = DigitalFootprint()
    relationships: list[RelationshipEdge] = []

    all_providers: set[str] = set()
    all_failed: set[str] = set()
    threat_scores: list[float] = []

    # Track known entities for identity
    known_emails: set[str] = set()
    known_ips: set[str] = set()
    known_domains: set[str] = set()
    known_companies: set[str] = set()

    if req.email:
        known_emails.add(req.email)
    if req.ip:
        known_ips.add(req.ip)
    if req.domain:
        known_domains.add(req.domain)
    if req.company:
        known_companies.add(req.company)

    for report in results:
        all_providers.update(report.providers_queried)
        all_failed.update(report.providers_failed)

        for r in report.reports:
            if isinstance(r, IPReport):
                ip_dict: dict[str, Any] = {
                    "ip": r.ip,
                    "provider": r.provider,
                    "hostnames": r.hostnames,
                    "os": r.os,
                    "tags": r.tags,
                }
                network.ips.append(ip_dict)
                known_ips.add(r.ip)

                # Ports
                for port in r.ports:
                    network.ports.append(port.model_dump(mode="json"))
                    network.services.append({
                        "port": port.port,
                        "service": port.service or port.product or "unknown",
                        "version": port.version,
                        "protocol": port.protocol,
                    })

                # Hostnames
                for h in r.hostnames:
                    if h not in network.hostnames:
                        network.hostnames.append(h)
                    known_domains.add(h)
                    relationships.append(RelationshipEdge(
                        source=r.ip, target=h,
                        relationship="resolves_to",
                        source_type="ip", target_type="domain",
                    ))

                # Geo
                if r.geo:
                    geo_dict: dict[str, Any] = {
                        "ip": r.ip,
                        "country": r.geo.country,
                        "country_code": r.geo.country_code,
                        "city": r.geo.city,
                        "latitude": r.geo.latitude,
                        "longitude": r.geo.longitude,
                        "asn": r.geo.asn,
                        "org": r.geo.org,
                    }
                    geo.locations.append(geo_dict)
                    if r.geo.org:
                        known_companies.add(r.geo.org)

                # Threats — vulnerabilities
                for vuln in r.vulns:
                    threats.vulnerabilities.append(vuln.model_dump(mode="json"))

                # Reputation
                if r.reputation_score is not None:
                    threat_scores.append(r.reputation_score * 100)

            elif isinstance(r, DomainReport):
                dom_dict: dict[str, Any] = {
                    "domain": r.domain,
                    "provider": r.provider,
                    "organization": r.organization,
                    "technologies": r.technologies,
                }
                domain_intel.domains.append(dom_dict)
                known_domains.add(r.domain)

                # Merge DNS
                for rtype, records in r.dns_records.items():
                    if rtype not in domain_intel.dns_records:
                        domain_intel.dns_records[rtype] = []
                    for rec in records:
                        if rec not in domain_intel.dns_records[rtype]:
                            domain_intel.dns_records[rtype].append(rec)

                # Subdomains
                for sub in r.subdomains:
                    if sub not in domain_intel.subdomains:
                        domain_intel.subdomains.append(sub)
                    known_domains.add(sub)
                    relationships.append(RelationshipEdge(
                        source=r.domain, target=sub,
                        relationship="has_subdomain",
                        source_type="domain", target_type="domain",
                    ))

                # Technologies
                for tech in r.technologies:
                    if tech not in domain_intel.technologies:
                        domain_intel.technologies.append(tech)

                # Emails from domain
                for email_contact in r.emails:
                    email_dict: dict[str, Any] = {
                        "email": email_contact.email,
                        "first_name": email_contact.first_name,
                        "last_name": email_contact.last_name,
                        "position": email_contact.position,
                        "department": email_contact.department,
                        "confidence": email_contact.confidence,
                    }
                    email_intel.emails.append(email_dict)
                    known_emails.add(email_contact.email)
                    relationships.append(RelationshipEdge(
                        source=r.domain, target=email_contact.email,
                        relationship="has_email",
                        source_type="domain", target_type="email",
                    ))

                # Organization
                if r.organization:
                    org_info.companies.append({
                        "name": r.organization,
                        "domain": r.domain,
                        "source": r.provider,
                    })
                    known_companies.add(r.organization)
                    relationships.append(RelationshipEdge(
                        source=r.domain, target=r.organization,
                        relationship="belongs_to",
                        source_type="domain", target_type="organization",
                    ))

                if r.reputation_score is not None:
                    threat_scores.append(r.reputation_score * 100)

            elif isinstance(r, EmailReport):
                verified_dict: dict[str, Any] = {
                    "email": r.email,
                    "provider": r.provider,
                    "deliverable": r.deliverable,
                    "disposable": r.disposable,
                    "first_name": r.first_name,
                    "last_name": r.last_name,
                    "organization": r.organization,
                    "confidence": r.confidence,
                    "sources": r.sources,
                }
                email_intel.verified.append(verified_dict)
                known_emails.add(r.email)

                if r.organization:
                    org_info.companies.append({
                        "name": r.organization,
                        "email": r.email,
                        "source": r.provider,
                    })
                    known_companies.add(r.organization)

                # Sources as digital footprint
                for source in r.sources:
                    if source and source not in footprint.sources:
                        footprint.sources.append(source)

            elif isinstance(r, URLReport):
                url_dict: dict[str, Any] = {
                    "url": r.url,
                    "provider": r.provider,
                    "malicious": r.malicious,
                    "categories": r.categories,
                    "screenshot_url": r.screenshot_url,
                }
                footprint.urls.append(url_dict)

                if r.malicious:
                    threats.malware_detected = True
                    threats.indicators.append(f"Malicious URL detected: {r.url}")

                if r.reputation_score is not None:
                    threat_scores.append(r.reputation_score * 100)

    # Merge social_media from request into digital footprint
    if req.social_media:
        footprint.social_media = dict(req.social_media)

    # Build identity
    identity.emails = sorted(known_emails)
    identity.phones = [req.phone] if req.phone else []
    identity.ips = sorted(known_ips)
    identity.domains = sorted(known_domains)
    identity.companies = sorted(known_companies)

    # Calculate threat score
    if threat_scores:
        # Invert: higher reputation = lower threat. Score as threat (0=safe, 100=dangerous)
        avg_rep = sum(threat_scores) / len(threat_scores)
        # Many APIs return 0-1 rep where higher = more trusted
        # Our UI wants threat score where higher = more dangerous
        threats.score = round(max(0, min(100, 100 - avg_rep)), 1)
    else:
        threats.score = 0

    if threats.vulnerabilities:
        threats.indicators.append(f"{len(threats.vulnerabilities)} vulnerabilities found")

    # Determine threat level
    if threats.score >= 75:
        threats.level = "critical"
    elif threats.score >= 50:
        threats.level = "high"
    elif threats.score >= 25:
        threats.level = "medium"
    else:
        threats.level = "low"

    # Build cross-entity relationships
    if req.name:
        for email in known_emails:
            relationships.append(RelationshipEdge(
                source=req.name, target=email,
                relationship="uses_email",
                source_type="person", target_type="email",
            ))
        for ip in known_ips:
            relationships.append(RelationshipEdge(
                source=req.name, target=ip,
                relationship="associated_ip",
                source_type="person", target_type="ip",
            ))

    if req.email and req.domain:
        relationships.append(RelationshipEdge(
            source=req.email, target=req.domain,
            relationship="email_domain",
            source_type="email", target_type="domain",
        ))

    return InvestigateResponse(
        identity=identity,
        network=network,
        threats=threats,
        geo=geo,
        email_intel=email_intel,
        phone_intel=phone_intel,
        domain_intel=domain_intel,
        organization=org_info,
        digital_footprint=footprint,
        relationships=relationships,
        providers_queried=sorted(all_providers),
        providers_failed=sorted(all_failed),
        query_count=len(tasks),
    )
