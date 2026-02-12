"""URLScan.io provider — URL and domain scanning/analysis."""

from __future__ import annotations

from typing import Any

from osint.core.cache import Cache
from osint.core.models import DomainReport, ReportType, URLReport
from osint.providers.base import BaseProvider


class URLScanProvider(BaseProvider):
    """URLScan.io API provider.

    Free tier limits (daily):
        Public scans: 5,000/day
        Search: 1,000/day
        Result retrieve: 10,000/day
    """

    @property
    def name(self) -> str:
        return "urlscan"

    @property
    def supported_types(self) -> list[str]:
        return ["url", "domain"]

    @property
    def rate_limit_config(self) -> dict[str, Any]:
        # 120 search/min, be conservative
        return {"rate": 2.0, "capacity": 5}

    def __init__(self, api_key: str, cache: Cache) -> None:
        self.api_key = api_key
        self.client = self._make_client(
            base_url="https://urlscan.io/api/v1",
            api_key=api_key,
            cache=cache,
            headers={"API-Key": api_key},
        )

    async def lookup(self, query: str, query_type: str) -> ReportType:
        if query_type == "url":
            return await self._url_search(query)
        elif query_type == "domain":
            return await self._domain_search(query)
        else:
            raise ValueError(f"URLScan does not support query type: {query_type}")

    async def _url_search(self, url: str) -> URLReport:
        """Search for existing scan results for a URL."""
        data = await self.client.get(
            "/search/",
            params={"q": f"page.url:\"{url}\"", "size": 1},
            query_type="url",
            query_value=url,
        )

        results = data.get("results", [])
        if not results:
            return URLReport(
                url=url,
                provider=self.name,
                raw=data,
            )

        result = results[0]
        task = result.get("task", {})
        page = result.get("page", {})
        verdicts = result.get("verdicts", {}).get("overall", {})

        malicious = verdicts.get("malicious", False)
        score = verdicts.get("score", 0)
        # Convert: 0 score = 1.0 reputation, 100 = 0.0
        reputation = 1.0 - (min(score, 100) / 100.0) if score else None

        categories = []
        if verdicts.get("categories"):
            categories = verdicts["categories"]
        if page.get("server"):
            categories.append(f"server:{page['server']}")

        screenshot_url = result.get("screenshot")

        return URLReport(
            url=url,
            provider=self.name,
            malicious=malicious,
            categories=categories,
            reputation_score=reputation,
            screenshot_url=screenshot_url,
            raw=result,
        )

    async def _domain_search(self, domain: str) -> DomainReport:
        """Search for existing scan results for a domain."""
        data = await self.client.get(
            "/search/",
            params={"q": f"domain:{domain}", "size": 5},
            query_type="domain",
            query_value=domain,
        )

        results = data.get("results", [])

        # Aggregate info from recent scans
        technologies: list[str] = []
        subdomains: set[str] = set()

        for result in results[:5]:
            page = result.get("page", {})
            if page.get("server") and page["server"] not in technologies:
                technologies.append(page["server"])
            if page.get("domain") and page["domain"] != domain:
                subdomains.add(page["domain"])

        # Check if any scans flagged malicious
        malicious_count = sum(
            1 for r in results
            if r.get("verdicts", {}).get("overall", {}).get("malicious", False)
        )
        reputation = 1.0 - (malicious_count / max(len(results), 1))

        return DomainReport(
            domain=domain,
            provider=self.name,
            subdomains=sorted(subdomains),
            technologies=technologies,
            reputation_score=reputation,
            raw=data,
        )

    async def close(self) -> None:
        await self.client.close()
