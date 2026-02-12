"""NumVerify provider — phone number validation and lookup."""

from __future__ import annotations

from typing import Any

from osint.core.cache import Cache
from osint.core.models import ReportType
from osint.providers.base import BaseProvider

# Phone reports use a custom model since it's not in the base set
from pydantic import BaseModel, Field


class PhoneReport(BaseModel):
    """Phone number intelligence report."""

    phone: str
    provider: str
    valid: bool | None = None
    number: str | None = None
    local_format: str | None = None
    international_format: str | None = None
    country_prefix: str | None = None
    country_code: str | None = None
    country_name: str | None = None
    location: str | None = None
    carrier: str | None = None
    line_type: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class NumVerifyProvider(BaseProvider):
    """NumVerify API provider.

    Free tier: 100 lookups/month. Use sparingly.
    Note: Free tier is HTTP only (no HTTPS).
    """

    @property
    def name(self) -> str:
        return "numverify"

    @property
    def supported_types(self) -> list[str]:
        return ["phone"]

    @property
    def rate_limit_config(self) -> dict[str, Any]:
        # 100/month ≈ 3/day, very conservative
        return {"rate": 0.1, "capacity": 2}

    def __init__(self, api_key: str, cache: Cache) -> None:
        self.api_key = api_key
        # Free tier only supports HTTP
        self.client = self._make_client(
            base_url="http://apilayer.net/api",
            api_key=api_key,
            cache=cache,
        )

    async def lookup(self, query: str, query_type: str) -> PhoneReport:
        if query_type == "phone":
            return await self._phone_lookup(query)
        else:
            raise ValueError(f"NumVerify does not support query type: {query_type}")

    async def _phone_lookup(self, phone: str) -> PhoneReport:
        data = await self.client.get(
            "/validate",
            params={"access_key": self.api_key, "number": phone},
            query_type="phone",
            query_value=phone,
        )

        if data.get("error"):
            return PhoneReport(
                phone=phone,
                provider=self.name,
                valid=False,
                raw=data,
            )

        return PhoneReport(
            phone=phone,
            provider=self.name,
            valid=data.get("valid"),
            number=data.get("number"),
            local_format=data.get("local_format"),
            international_format=data.get("international_format"),
            country_prefix=data.get("country_prefix"),
            country_code=data.get("country_code"),
            country_name=data.get("country_name"),
            location=data.get("location"),
            carrier=data.get("carrier"),
            line_type=data.get("line_type"),
            raw=data,
        )

    async def close(self) -> None:
        await self.client.close()
