"""Shodan provider — IP/host lookup, search, DNS resolve."""

from __future__ import annotations

from typing import Any

from osint.core.cache import Cache
from osint.core.models import (
    GeoLocation,
    IPReport,
    DomainReport,
    PortInfo,
    ReportType,
    Vulnerability,
)
from osint.providers.base import BaseProvider


class ShodanProvider(BaseProvider):
    """Shodan.io OSINT provider."""

    @property
    def name(self) -> str:
        return "shodan"

    @property
    def supported_types(self) -> list[str]:
        return ["ip", "domain"]

    @property
    def rate_limit_config(self) -> dict[str, Any]:
        return {"rate": 1.0, "capacity": 1}  # 1 req/sec

    def __init__(self, api_key: str, cache: Cache) -> None:
        self.api_key = api_key
        self.client = self._make_client(
            base_url="https://api.shodan.io",
            api_key=api_key,
            cache=cache,
        )

    async def lookup(self, query: str, query_type: str) -> ReportType:
        """Perform a Shodan lookup.

        Supports:
            - ip: Host information lookup
            - domain: DNS resolve
        """
        if query_type == "ip":
            return await self._ip_lookup(query)
        elif query_type == "domain":
            return await self._dns_resolve(query)
        else:
            raise ValueError(f"Shodan does not support query type: {query_type}")

    async def _ip_lookup(self, ip: str) -> IPReport:
        """Look up host information for an IP address."""
        data = await self.client.get(
            f"/shodan/host/{ip}",
            params={"key": self.api_key},
            query_type="ip",
            query_value=ip,
        )

        ports = []
        vulns_set: set[str] = set()
        for item in data.get("data", []):
            ports.append(
                PortInfo(
                    port=item.get("port", 0),
                    protocol=item.get("transport", "tcp"),
                    product=item.get("product"),
                    version=item.get("version"),
                    banner=item.get("data", "")[:500],
                )
            )
            for v in item.get("vulns", {}):
                vulns_set.add(v)

        vulns = [Vulnerability(cve_id=v) for v in sorted(vulns_set)]

        geo = GeoLocation(
            country=data.get("country_name"),
            country_code=data.get("country_code"),
            city=data.get("city"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            org=data.get("org"),
            asn=data.get("asn"),
        )

        return IPReport(
            ip=ip,
            provider=self.name,
            hostnames=data.get("hostnames", []),
            ports=ports,
            vulns=vulns,
            geo=geo,
            os=data.get("os"),
            tags=data.get("tags", []),
            raw=data,
        )

    async def _dns_resolve(self, domain: str) -> DomainReport:
        """Resolve DNS for a domain via Shodan."""
        data = await self.client.get(
            "/dns/resolve",
            params={"hostnames": domain, "key": self.api_key},
            query_type="domain_dns",
            query_value=domain,
        )

        dns_records: dict[str, list[str]] = {}
        if domain in data:
            dns_records["A"] = [data[domain]]

        return DomainReport(
            domain=domain,
            provider=self.name,
            dns_records=dns_records,
            raw=data,
        )

    async def close(self) -> None:
        await self.client.close()
