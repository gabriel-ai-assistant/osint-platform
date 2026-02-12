"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from osint.api.models import HealthResponse
from osint.config import get_settings
from osint.providers import ALL_PROVIDERS

router = APIRouter()

# Map provider class names to settings key attrs
_KEY_MAP: dict[str, str] = {
    "shodan": "shodan_api_key",
    "hunter": "hunter_api_key",
    "virustotal": "virustotal_api_key",
    "otx": "otx_api_key",
    "abuseipdb": "abuseipdb_api_key",
    "urlscan": "urlscan_api_key",
    "ipinfo": "ipinfo_token",
    "numverify": "numverify_api_key",
    "opencorporates": "opencorporates_api_key",
}


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    settings = get_settings()
    available = 0
    for cls in ALL_PROVIDERS:
        name = cls.__name__.replace("Provider", "").lower()
        key_attr = _KEY_MAP.get(name, f"{name}_api_key")
        if getattr(settings, key_attr, ""):
            available += 1

    return HealthResponse(
        status="ok",
        version="0.1.0",
        providers_available=available,
    )
