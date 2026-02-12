"""VirusTotal provider — IP, domain, URL, and file hash lookups."""

from __future__ import annotations

from typing import Any

from osint.core.cache import Cache
from osint.core.models import (
    DomainReport,
    GeoLocation,
    IPReport,
    ReportType,
    URLReport,
)
from osint.providers.base import BaseProvider


class VirusTotalProvider(BaseProvider):
    """VirusTotal v3 API provider.

    Free tier: 4 lookups/min, 500/day, 15.5k/month.
    """

    @property
    def name(self) -> str:
        return "virustotal"

    @property
    def supported_types(self) -> list[str]:
        return ["ip", "domain", "url"]

    @property
    def rate_limit_config(self) -> dict[str, Any]:
        # 4 per minute = 1 per 15 seconds
        return {"rate": 1 / 15, "capacity": 4}

    def __init__(self, api_key: str, cache: Cache) -> None:
        self.api_key = api_key
        self.client = self._make_client(
            base_url="https://www.virustotal.com/api/v3",
            api_key=api_key,
            cache=cache,
            headers={"x-apikey": api_key},
        )

    async def lookup(self, query: str, query_type: str) -> ReportType:
        if query_type == "ip":
            return await self._ip_lookup(query)
        elif query_type == "domain":
            return await self._domain_lookup(query)
        elif query_type == "url":
            return await self._url_lookup(query)
        else:
            raise ValueError(f"VirusTotal does not support query type: {query_type}")

    async def _ip_lookup(self, ip: str) -> IPReport:
        data = await self.client.get(
            f"/ip_addresses/{ip}",
            query_type="ip",
            query_value=ip,
        )
        attrs = data.get("data", {}).get("attributes", {})
        stats = attrs.get("last_analysis_stats", {})

        malicious = stats.get("malicious", 0)
        total = sum(stats.values()) if stats else 0
        reputation = 1.0 - (malicious / total) if total > 0 else None

        geo = GeoLocation(
            country=attrs.get("country"),
            country_code=attrs.get("country"),
            asn=str(attrs.get("asn", "")),
            org=attrs.get("as_owner"),
        )

        return IPReport(
            ip=ip,
            provider=self.name,
            hostnames=[],
            geo=geo,
            reputation_score=reputation,
            tags=attrs.get("tags", []),
            raw=data,
        )

    async def _domain_lookup(self, domain: str) -> DomainReport:
        data = await self.client.get(
            f"/domains/{domain}",
            query_type="domain",
            query_value=domain,
        )
        attrs = data.get("data", {}).get("attributes", {})
        stats = attrs.get("last_analysis_stats", {})

        malicious = stats.get("malicious", 0)
        total = sum(stats.values()) if stats else 0
        reputation = 1.0 - (malicious / total) if total > 0 else None

        dns_records: dict[str, list[str]] = {}
        for record in attrs.get("last_dns_records", []):
            rtype = record.get("type", "UNKNOWN")
            dns_records.setdefault(rtype, []).append(record.get("value", ""))

        categories = []
        for cat_dict in [attrs.get("categories", {})]:
            if isinstance(cat_dict, dict):
                categories.extend(cat_dict.values())

        return DomainReport(
            domain=domain,
            provider=self.name,
            organization=attrs.get("registrar"),
            dns_records=dns_records,
            technologies=[],
            reputation_score=reputation,
            raw=data,
        )

    async def _url_lookup(self, url: str) -> URLReport:
        """Look up a URL by its ID (base64url of the URL without padding)."""
        import base64

        url_id = base64.urlsafe_b64encode(url.encode()).rstrip(b"=").decode()
        data = await self.client.get(
            f"/urls/{url_id}",
            query_type="url",
            query_value=url,
        )
        attrs = data.get("data", {}).get("attributes", {})
        stats = attrs.get("last_analysis_stats", {})

        malicious_count = stats.get("malicious", 0)
        total = sum(stats.values()) if stats else 0
        reputation = 1.0 - (malicious_count / total) if total > 0 else None

        categories = []
        for cat_dict in [attrs.get("categories", {})]:
            if isinstance(cat_dict, dict):
                categories.extend(cat_dict.values())

        return URLReport(
            url=url,
            provider=self.name,
            malicious=malicious_count > 0,
            categories=categories,
            reputation_score=reputation,
            raw=data,
        )

    async def close(self) -> None:
        await self.client.close()
