"""IPInfo.io provider — IP geolocation, ASN, company data."""

from __future__ import annotations

from typing import Any

from osint.core.cache import Cache
from osint.core.models import GeoLocation, IPReport, ReportType
from osint.providers.base import BaseProvider


class IPInfoProvider(BaseProvider):
    """IPInfo.io API provider.

    Free tier: 50,000 lookups/month.
    Excellent geolocation, ASN, and company data.
    """

    @property
    def name(self) -> str:
        return "ipinfo"

    @property
    def supported_types(self) -> list[str]:
        return ["ip"]

    @property
    def rate_limit_config(self) -> dict[str, Any]:
        # 50k/month ≈ ~1600/day, be conservative
        return {"rate": 2.0, "capacity": 5}

    def __init__(self, api_key: str, cache: Cache) -> None:
        self.api_key = api_key
        self.client = self._make_client(
            base_url="https://ipinfo.io",
            api_key=api_key,
            cache=cache,
            headers={"Authorization": f"Bearer {api_key}"},
        )

    async def lookup(self, query: str, query_type: str) -> ReportType:
        if query_type == "ip":
            return await self._ip_lookup(query)
        else:
            raise ValueError(f"IPInfo does not support query type: {query_type}")

    async def _ip_lookup(self, ip: str) -> IPReport:
        data = await self.client.get(
            f"/{ip}/json",
            query_type="ip",
            query_value=ip,
        )

        lat, lon = None, None
        loc = data.get("loc", "")
        if "," in loc:
            parts = loc.split(",")
            try:
                lat, lon = float(parts[0]), float(parts[1])
            except (ValueError, IndexError):
                pass

        geo = GeoLocation(
            country=data.get("country"),
            country_code=data.get("country"),
            city=data.get("city"),
            latitude=lat,
            longitude=lon,
            org=data.get("org"),
            asn=data.get("org", "").split(" ")[0] if data.get("org") else None,
        )

        hostnames = []
        if data.get("hostname"):
            hostnames.append(data["hostname"])

        tags = []
        if data.get("privacy", {}).get("vpn"):
            tags.append("vpn")
        if data.get("privacy", {}).get("proxy"):
            tags.append("proxy")
        if data.get("privacy", {}).get("tor"):
            tags.append("tor")
        if data.get("privacy", {}).get("hosting"):
            tags.append("hosting")
        if data.get("region"):
            tags.append(f"region:{data['region']}")

        return IPReport(
            ip=ip,
            provider=self.name,
            hostnames=hostnames,
            geo=geo,
            tags=tags,
            raw=data,
        )

    async def close(self) -> None:
        await self.client.close()
