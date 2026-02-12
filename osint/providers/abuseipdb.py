"""AbuseIPDB provider — IP reputation and abuse reports."""

from __future__ import annotations

from typing import Any

from osint.core.cache import Cache
from osint.core.models import GeoLocation, IPReport, ReportType
from osint.providers.base import BaseProvider


class AbuseIPDBProvider(BaseProvider):
    """AbuseIPDB v2 API provider.

    Free tier daily limits:
        check: 1,000/day
        check-block: 100/day
        report: 1,000/day
        blacklist: 5/day
    """

    @property
    def name(self) -> str:
        return "abuseipdb"

    @property
    def supported_types(self) -> list[str]:
        return ["ip"]

    @property
    def rate_limit_config(self) -> dict[str, Any]:
        # Conservative: ~1 req/sec, well within 1000/day
        return {"rate": 1.0, "capacity": 5}

    def __init__(self, api_key: str, cache: Cache) -> None:
        self.api_key = api_key
        self.client = self._make_client(
            base_url="https://api.abuseipdb.com/api/v2",
            api_key=api_key,
            cache=cache,
            headers={"Key": api_key, "Accept": "application/json"},
        )

    async def lookup(self, query: str, query_type: str) -> ReportType:
        if query_type == "ip":
            return await self._ip_check(query)
        else:
            raise ValueError(f"AbuseIPDB does not support query type: {query_type}")

    async def _ip_check(self, ip: str) -> IPReport:
        """Check an IP address for abuse reports."""
        data = await self.client.get(
            "/check",
            params={"ipAddress": ip, "maxAgeInDays": 90, "verbose": ""},
            query_type="ip",
            query_value=ip,
        )
        d = data.get("data", {})

        abuse_score = d.get("abuseConfidenceScore", 0)
        # Convert: 0 abuse = 1.0 reputation, 100 abuse = 0.0 reputation
        reputation = 1.0 - (abuse_score / 100.0)

        geo = GeoLocation(
            country=d.get("countryName"),
            country_code=d.get("countryCode"),
        )

        tags = []
        if d.get("isWhitelisted"):
            tags.append("whitelisted")
        if d.get("isTor"):
            tags.append("tor-exit-node")
        if d.get("usageType"):
            tags.append(d["usageType"])
        if d.get("domain"):
            tags.append(f"domain:{d['domain']}")

        total_reports = d.get("totalReports", 0)
        hostnames = []
        if d.get("domain"):
            hostnames.append(d["domain"])

        return IPReport(
            ip=ip,
            provider=self.name,
            hostnames=hostnames,
            geo=geo,
            reputation_score=reputation,
            tags=tags,
            raw=data,
        )

    async def close(self) -> None:
        await self.client.close()
