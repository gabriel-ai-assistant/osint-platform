"""AlienVault OTX provider — IP, domain, URL threat intelligence."""

from __future__ import annotations

from typing import Any

from osint.core.cache import Cache
from osint.core.models import (
    DomainReport,
    GeoLocation,
    IPReport,
    ReportType,
    URLReport,
    Vulnerability,
)
from osint.providers.base import BaseProvider


class OTXProvider(BaseProvider):
    """AlienVault Open Threat Exchange provider.

    Completely free — no rate limits documented, but be respectful.
    Provides: IP reputation, domain intel, URL analysis, pulse/IOC feeds.
    """

    @property
    def name(self) -> str:
        return "otx"

    @property
    def supported_types(self) -> list[str]:
        return ["ip", "domain", "url"]

    @property
    def rate_limit_config(self) -> dict[str, Any]:
        # OTX is free but let's be respectful — 2 req/sec
        return {"rate": 2.0, "capacity": 5}

    def __init__(self, api_key: str, cache: Cache) -> None:
        self.api_key = api_key
        self.client = self._make_client(
            base_url="https://otx.alienvault.com/api/v1",
            api_key=api_key,
            cache=cache,
            headers={"X-OTX-API-KEY": api_key},
        )

    async def lookup(self, query: str, query_type: str) -> ReportType:
        if query_type == "ip":
            return await self._ip_lookup(query)
        elif query_type == "domain":
            return await self._domain_lookup(query)
        elif query_type == "url":
            return await self._url_lookup(query)
        else:
            raise ValueError(f"OTX does not support query type: {query_type}")

    async def _ip_lookup(self, ip: str) -> IPReport:
        """Lookup IP via OTX — combines general + reputation + geo sections."""
        general = await self.client.get(
            f"/indicators/IPv4/{ip}/general",
            query_type="ip",
            query_value=f"{ip}_general",
        )

        # Pulse count is a good reputation signal
        pulse_count = general.get("pulse_info", {}).get("count", 0)
        # More pulses = more malicious activity reported
        reputation = max(0.0, 1.0 - min(pulse_count / 20, 1.0))

        geo_data = general.get("geo", {}) if "geo" in general else {}
        geo = GeoLocation(
            country=general.get("country_name") or geo_data.get("country_name"),
            country_code=general.get("country_code") or geo_data.get("country_code"),
            city=general.get("city") or geo_data.get("city"),
            latitude=general.get("latitude") or geo_data.get("latitude"),
            longitude=general.get("longitude") or geo_data.get("longitude"),
            asn=general.get("asn"),
        )

        # Extract CVEs from pulses
        vulns = []
        for pulse in general.get("pulse_info", {}).get("pulses", [])[:10]:
            for tag in pulse.get("tags", []):
                if tag.upper().startswith("CVE-"):
                    vulns.append(Vulnerability(cve_id=tag.upper()))

        # Deduplicate vulns
        seen = set()
        unique_vulns = []
        for v in vulns:
            if v.cve_id not in seen:
                seen.add(v.cve_id)
                unique_vulns.append(v)

        return IPReport(
            ip=ip,
            provider=self.name,
            vulns=unique_vulns,
            geo=geo,
            reputation_score=reputation,
            tags=[p.get("name", "") for p in general.get("pulse_info", {}).get("pulses", [])[:5]],
            raw=general,
        )

    async def _domain_lookup(self, domain: str) -> DomainReport:
        general = await self.client.get(
            f"/indicators/domain/{domain}/general",
            query_type="domain",
            query_value=f"{domain}_general",
        )

        pulse_count = general.get("pulse_info", {}).get("count", 0)
        reputation = max(0.0, 1.0 - min(pulse_count / 20, 1.0))

        # Get DNS records from passive_dns section
        dns_records: dict[str, list[str]] = {}
        try:
            passive = await self.client.get(
                f"/indicators/domain/{domain}/passive_dns",
                query_type="domain_dns",
                query_value=f"{domain}_pdns",
            )
            for record in passive.get("passive_dns", [])[:20]:
                rtype = record.get("record_type", "A")
                dns_records.setdefault(rtype, []).append(record.get("address", ""))
        except Exception:
            pass

        return DomainReport(
            domain=domain,
            provider=self.name,
            dns_records=dns_records,
            reputation_score=reputation,
            raw=general,
        )

    async def _url_lookup(self, url: str) -> URLReport:
        general = await self.client.get(
            f"/indicators/url/{url}/general",
            query_type="url",
            query_value=url,
        )

        pulse_count = general.get("pulse_info", {}).get("count", 0)
        reputation = max(0.0, 1.0 - min(pulse_count / 20, 1.0))

        return URLReport(
            url=url,
            provider=self.name,
            malicious=pulse_count > 0,
            reputation_score=reputation,
            raw=general,
        )

    async def close(self) -> None:
        await self.client.close()
