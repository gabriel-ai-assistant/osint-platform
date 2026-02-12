"""Base async HTTP client with rate limiting, retries, and caching."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from osint.core.cache import Cache
from osint.core.rate_limiter import TokenBucketRateLimiter

logger = logging.getLogger(__name__)


class OSINTClient:
    """Async HTTP client with built-in rate limiting, retries, and caching.

    Args:
        base_url: API base URL.
        rate_limiter: Rate limiter instance for this provider.
        cache: Shared cache instance.
        provider_name: Name for cache keys and logging.
        headers: Default request headers.
        max_retries: Maximum retry attempts on failure.
        cache_ttl: Default cache TTL in seconds.
    """

    def __init__(
        self,
        base_url: str,
        rate_limiter: TokenBucketRateLimiter,
        cache: Cache,
        provider_name: str,
        headers: dict[str, str] | None = None,
        max_retries: int = 3,
        cache_ttl: int = 3600,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.rate_limiter = rate_limiter
        self.cache = cache
        self.provider_name = provider_name
        self.max_retries = max_retries
        self.cache_ttl = cache_ttl
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers or {},
            timeout=30.0,
        )

    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        query_type: str = "default",
        query_value: str = "",
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """Make a cached, rate-limited GET request with retries.

        Args:
            path: URL path relative to base_url.
            params: Query parameters.
            query_type: Cache key component (e.g., "ip_lookup").
            query_value: Cache key component (e.g., the IP address).
            use_cache: Whether to check/store in cache.

        Returns:
            Parsed JSON response.
        """
        # Check cache first
        if use_cache:
            cached = self.cache.get(self.provider_name, query_type, query_value)
            if cached is not None:
                logger.debug("Cache hit: %s/%s/%s", self.provider_name, query_type, query_value)
                return cached

        # Rate limit
        await self.rate_limiter.acquire()

        # Retry loop
        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    "Request: %s %s%s (attempt %d)",
                    self.provider_name,
                    self.base_url,
                    path,
                    attempt + 1,
                )
                resp = await self._client.get(path, params=params)
                resp.raise_for_status()
                data: dict[str, Any] = resp.json()

                # Cache the result
                if use_cache:
                    self.cache.set(
                        self.provider_name, query_type, query_value, data, ttl=self.cache_ttl
                    )

                return data

            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code in (401, 403):
                    raise  # Don't retry auth errors
                if e.response.status_code == 429:
                    # Rate limited — wait and retry
                    await self.rate_limiter.acquire()
                    continue
                if e.response.status_code >= 500:
                    continue  # Retry server errors
                raise

            except (httpx.ConnectError, httpx.ReadTimeout) as e:
                last_error = e
                continue

        raise RuntimeError(
            f"{self.provider_name}: request failed after {self.max_retries} retries: {last_error}"
        )

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()
