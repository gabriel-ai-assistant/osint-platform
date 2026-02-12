"""Tests for the base OSINT client."""

from __future__ import annotations

import pytest

from osint.core.cache import Cache
from osint.core.rate_limiter import TokenBucketRateLimiter


class TestCache:
    def test_set_and_get(self, tmp_path):
        cache = Cache(db_path=tmp_path / "test.db")
        cache.set("test_provider", "ip", "1.1.1.1", {"result": "ok"}, ttl=3600)
        result = cache.get("test_provider", "ip", "1.1.1.1")
        assert result == {"result": "ok"}
        cache.close()

    def test_get_missing(self, tmp_path):
        cache = Cache(db_path=tmp_path / "test.db")
        result = cache.get("test_provider", "ip", "2.2.2.2")
        assert result is None
        cache.close()

    def test_expired_entry(self, tmp_path):
        cache = Cache(db_path=tmp_path / "test.db")
        cache.set("test_provider", "ip", "1.1.1.1", {"result": "ok"}, ttl=-1)
        result = cache.get("test_provider", "ip", "1.1.1.1")
        assert result is None
        cache.close()

    def test_clear(self, tmp_path):
        cache = Cache(db_path=tmp_path / "test.db")
        cache.set("p", "t", "v", {"x": 1})
        cache.clear()
        assert cache.get("p", "t", "v") is None
        cache.close()


class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_acquire(self):
        limiter = TokenBucketRateLimiter(rate=100.0, capacity=5)
        # Should not block with high rate
        for _ in range(5):
            await limiter.acquire()
