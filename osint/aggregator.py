"""Aggregator — fan out queries to providers and merge results."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

from osint.config import Settings
from osint.core.cache import Cache
from osint.core.models import AggregatedReport, ReportType
from osint.providers import ALL_PROVIDERS
from osint.providers.base import BaseProvider

logger = logging.getLogger(__name__)

# API key field mapping (provider name → settings attribute)
_KEY_MAP: dict[str, str] = {
    "shodan": "shodan_api_key",
    "hunter": "hunter_api_key",
    "virustotal": "virustotal_api_key",
    "otx": "otx_api_key",
    "abuseipdb": "abuseipdb_api_key",
    "urlscan": "urlscan_api_key",
    "ipinfo": "ipinfo_token",
}


def detect_query_type(query: str) -> str:
    """Auto-detect query type from the input string."""
    # IP address
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", query):
        return "ip"
    # Email
    if "@" in query and "." in query.split("@")[-1]:
        return "email"
    # URL
    if query.startswith(("http://", "https://")):
        return "url"
    # Domain (fallback)
    if "." in query:
        return "domain"
    return "unknown"


def _build_providers(settings: Settings, cache: Cache) -> list[BaseProvider]:
    """Instantiate all providers that have valid API keys."""
    providers: list[BaseProvider] = []
    for cls in ALL_PROVIDERS:
        # We need to instantiate temporarily to get the name
        name = cls.__name__.replace("Provider", "").lower()
        key_attr = _KEY_MAP.get(name, f"{name}_api_key")
        api_key = getattr(settings, key_attr, "")
        if not api_key:
            logger.warning("Skipping %s: no API key configured", name)
            continue
        providers.append(cls(api_key=api_key, cache=cache))
    return providers


async def aggregate(
    query: str,
    query_type: str | None = None,
    settings: Settings | None = None,
) -> AggregatedReport:
    """Query all applicable providers and merge results.

    Args:
        query: The search term (IP, domain, email, URL).
        query_type: Override auto-detection.
        settings: App settings (loaded from env if None).

    Returns:
        AggregatedReport with all provider results merged.
    """
    from osint.config import get_settings

    if settings is None:
        settings = get_settings()

    if query_type is None:
        query_type = detect_query_type(query)

    cache = Cache(db_path=f"{settings.cache_dir}/cache.db")
    providers = _build_providers(settings, cache)

    # Filter to providers supporting this query type
    applicable = [p for p in providers if query_type in p.supported_types]

    report = AggregatedReport(
        query=query,
        query_type=query_type,
        providers_queried=[p.name for p in applicable],
    )

    if not applicable:
        logger.warning("No providers available for query type: %s", query_type)
        return report

    # Fan out queries concurrently
    async def _query_provider(provider: BaseProvider) -> tuple[str, ReportType | None, str | None]:
        try:
            result = await provider.lookup(query, query_type)
            return (provider.name, result, None)
        except Exception as e:
            logger.error("Provider %s failed: %s", provider.name, e)
            return (provider.name, None, str(e))

    tasks = [_query_provider(p) for p in applicable]
    results = await asyncio.gather(*tasks)

    for name, result, error in results:
        if result is not None:
            report.reports.append(result)
        if error is not None:
            report.providers_failed.append(name)

    report.confidence = report.merge_confidence()

    # Cleanup
    for p in providers:
        await p.close()
    cache.close()

    return report
