"""Token bucket rate limiter for API providers."""

from __future__ import annotations

import asyncio
import time


class TokenBucketRateLimiter:
    """Rate limiter using the token bucket algorithm.

    Args:
        rate: Number of tokens added per second.
        capacity: Maximum bucket capacity (burst size).
    """

    def __init__(self, rate: float, capacity: int = 1) -> None:
        self.rate = rate
        self.capacity = capacity
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self._last_refill = now

    async def acquire(self) -> None:
        """Wait until a token is available, then consume it."""
        async with self._lock:
            self._refill()
            if self._tokens < 1:
                wait_time = (1 - self._tokens) / self.rate
                await asyncio.sleep(wait_time)
                self._refill()
            self._tokens -= 1


class RateLimiterRegistry:
    """Manages per-provider rate limiters."""

    def __init__(self) -> None:
        self._limiters: dict[str, TokenBucketRateLimiter] = {}

    def get(self, provider: str, rate: float, capacity: int = 1) -> TokenBucketRateLimiter:
        """Get or create a rate limiter for a provider."""
        if provider not in self._limiters:
            self._limiters[provider] = TokenBucketRateLimiter(rate=rate, capacity=capacity)
        return self._limiters[provider]


# Global registry
registry = RateLimiterRegistry()
