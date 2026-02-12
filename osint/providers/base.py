"""Abstract base class for OSINT providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from osint.core.cache import Cache
from osint.core.client import OSINTClient
from osint.core.models import ReportType
from osint.core.rate_limiter import TokenBucketRateLimiter


class BaseProvider(ABC):
    """Base class all OSINT providers must implement.

    Subclasses define their name, supported query types, and lookup logic.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g., 'shodan')."""

    @property
    @abstractmethod
    def supported_types(self) -> list[str]:
        """Query types this provider handles (e.g., ['ip', 'domain'])."""

    @property
    @abstractmethod
    def rate_limit_config(self) -> dict[str, Any]:
        """Rate limiter config: {'rate': float, 'capacity': int}."""

    @abstractmethod
    def __init__(self, api_key: str, cache: Cache) -> None:
        """Initialize with API key and shared cache."""

    @abstractmethod
    async def lookup(self, query: str, query_type: str) -> ReportType:
        """Perform a lookup and return a normalized report.

        Args:
            query: The search query (IP, domain, email, etc.).
            query_type: Type of query ('ip', 'domain', 'email', 'url').

        Returns:
            A normalized report model.

        Raises:
            ValueError: If query_type is not supported.
        """

    def _make_client(
        self, base_url: str, api_key: str, cache: Cache, headers: dict[str, str] | None = None
    ) -> OSINTClient:
        """Create an OSINTClient with this provider's rate limit config."""
        limiter = TokenBucketRateLimiter(
            rate=self.rate_limit_config["rate"],
            capacity=self.rate_limit_config.get("capacity", 1),
        )
        return OSINTClient(
            base_url=base_url,
            rate_limiter=limiter,
            cache=cache,
            provider_name=self.name,
            headers=headers,
        )

    async def close(self) -> None:
        """Clean up resources."""
