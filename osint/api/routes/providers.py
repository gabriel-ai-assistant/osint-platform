"""Providers listing endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from osint.api.models import ProviderInfo, ProvidersResponse
from osint.config import get_settings
from osint.core.cache import Cache
from osint.providers import ALL_PROVIDERS

router = APIRouter()

_KEY_MAP: dict[str, str | None] = {
    "shodan": "shodan_api_key",
    "hunter": "hunter_api_key",
    "virustotal": "virustotal_api_key",
    "otx": "otx_api_key",
    "abuseipdb": "abuseipdb_api_key",
    "urlscan": "urlscan_api_key",
    "ipinfo": "ipinfo_token",
    "numverify": "numverify_api_key",
    "opencorporates": "opencorporates_api_key",
    "sherlock": None,
    "maigret": None,
    "holehe": None,
}

# Providers that don't need API keys (CLI tools)
_NO_KEY_PROVIDERS = {"sherlock", "maigret", "holehe"}


@router.get("/providers", response_model=ProvidersResponse)
async def list_providers() -> ProvidersResponse:
    """List all providers and their configuration status."""
    settings = get_settings()
    providers: list[ProviderInfo] = []

    for cls in ALL_PROVIDERS:
        name = cls.__name__.replace("Provider", "").lower()
        key_attr = _KEY_MAP.get(name, f"{name}_api_key")
        if name in _NO_KEY_PROVIDERS:
            has_key = True  # CLI tools, no API key needed
        elif key_attr is None:
            has_key = True
        else:
            has_key = bool(getattr(settings, key_attr, ""))

        # Instantiate to get metadata
        cache = Cache(db_path=f"{settings.cache_dir}/cache.db")
        try:
            instance = cls(api_key=getattr(settings, key_attr, "") or "", cache=cache)
            supported = instance.supported_types
            rate_limit = instance.rate_limit_config
            await instance.close()
        except Exception:
            supported = []
            rate_limit = {}
        finally:
            cache.close()

        providers.append(
            ProviderInfo(
                name=name,
                available=has_key,
                supported_types=supported,
                rate_limit=rate_limit,
            )
        )

    available_count = sum(1 for p in providers if p.available)
    return ProvidersResponse(
        providers=providers,
        total=len(providers),
        available=available_count,
    )
