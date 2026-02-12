"""Hunter.io provider — domain search, email finder, email verifier."""

from __future__ import annotations

from typing import Any

from osint.core.cache import Cache
from osint.core.models import (
    DomainReport,
    EmailContact,
    EmailReport,
    ReportType,
)
from osint.providers.base import BaseProvider


class HunterProvider(BaseProvider):
    """Hunter.io OSINT provider."""

    @property
    def name(self) -> str:
        return "hunter"

    @property
    def supported_types(self) -> list[str]:
        return ["domain", "email"]

    @property
    def rate_limit_config(self) -> dict[str, Any]:
        return {"rate": 10 / 60, "capacity": 2}  # 10 req/min

    def __init__(self, api_key: str, cache: Cache) -> None:
        self.api_key = api_key
        self.client = self._make_client(
            base_url="https://api.hunter.io",
            api_key=api_key,
            cache=cache,
        )

    async def lookup(self, query: str, query_type: str) -> ReportType:
        """Perform a Hunter.io lookup.

        Supports:
            - domain: Domain search (find emails)
            - email: Email verification
        """
        if query_type == "domain":
            return await self._domain_search(query)
        elif query_type == "email":
            return await self._email_verify(query)
        else:
            raise ValueError(f"Hunter does not support query type: {query_type}")

    async def _domain_search(self, domain: str) -> DomainReport:
        """Search for email addresses associated with a domain."""
        data = await self.client.get(
            "/v2/domain-search",
            params={"domain": domain, "api_key": self.api_key},
            query_type="domain",
            query_value=domain,
        )

        result = data.get("data", {})
        emails = [
            EmailContact(
                email=e.get("value", ""),
                first_name=e.get("first_name"),
                last_name=e.get("last_name"),
                position=e.get("position"),
                department=e.get("department"),
                confidence=e.get("confidence"),
                sources=[s.get("domain", "") for s in e.get("sources", [])],
            )
            for e in result.get("emails", [])
        ]

        return DomainReport(
            domain=domain,
            provider=self.name,
            organization=result.get("organization"),
            emails=emails,
            technologies=result.get("technologies", []),
            raw=data,
        )

    async def _email_verify(self, email: str) -> EmailReport:
        """Verify an email address."""
        data = await self.client.get(
            "/v2/email-verifier",
            params={"email": email, "api_key": self.api_key},
            query_type="email",
            query_value=email,
        )

        result = data.get("data", {})
        return EmailReport(
            email=email,
            provider=self.name,
            deliverable=result.get("result") == "deliverable",
            disposable=result.get("disposable"),
            first_name=result.get("first_name"),
            last_name=result.get("last_name"),
            organization=result.get("organization"),
            sources=[s.get("domain", "") for s in result.get("sources", [])],
            confidence=result.get("score"),
            raw=data,
        )

    async def close(self) -> None:
        await self.client.close()
