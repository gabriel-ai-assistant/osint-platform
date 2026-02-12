"""OpenCorporates provider — company/corporate lookups (no API key needed)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from osint.core.cache import Cache
from osint.core.models import ReportType
from osint.providers.base import BaseProvider


class CompanyReport(BaseModel):
    """Company intelligence report."""

    query: str
    provider: str
    companies: list[dict[str, Any]] = Field(default_factory=list)
    total_results: int = 0
    raw: dict[str, Any] = Field(default_factory=dict)


class OpenCorporatesProvider(BaseProvider):
    """OpenCorporates API provider.

    Requires API key (free tier locked down).
    Rate limited — be conservative.
    """

    @property
    def name(self) -> str:
        return "opencorporates"

    @property
    def supported_types(self) -> list[str]:
        return ["company"]

    @property
    def rate_limit_config(self) -> dict[str, Any]:
        # No documented limits but be respectful
        return {"rate": 0.5, "capacity": 2}

    def __init__(self, api_key: str, cache: Cache) -> None:
        self.api_key = api_key
        self.client = self._make_client(
            base_url="https://api.opencorporates.com/v0.4",
            api_key=api_key,
            cache=cache,
        )

    async def lookup(self, query: str, query_type: str) -> CompanyReport:
        if query_type == "company":
            return await self._company_search(query)
        else:
            raise ValueError(f"OpenCorporates does not support query type: {query_type}")

    async def _company_search(self, query: str) -> CompanyReport:
        data = await self.client.get(
            "/companies/search",
            params={"q": query, "per_page": 10, "api_token": self.api_key},
            query_type="company",
            query_value=query,
        )

        results = data.get("results", {})
        companies_raw = results.get("companies", [])
        total = results.get("total_count", 0)

        companies = []
        for item in companies_raw:
            c = item.get("company", {})
            companies.append({
                "name": c.get("name"),
                "company_number": c.get("company_number"),
                "jurisdiction": c.get("jurisdiction_code"),
                "status": c.get("current_status"),
                "type": c.get("company_type"),
                "incorporation_date": c.get("incorporation_date"),
                "dissolution_date": c.get("dissolution_date"),
                "registered_address": c.get("registered_address_in_full"),
                "url": c.get("opencorporates_url"),
            })

        return CompanyReport(
            query=query,
            provider=self.name,
            companies=companies,
            total_results=total,
            raw=data,
        )

    async def close(self) -> None:
        await self.client.close()
