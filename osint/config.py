"""Configuration management via pydantic-settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Provider API keys
    shodan_api_key: str = ""
    hunter_api_key: str = ""
    virustotal_api_key: str = ""
    censys_api_id: str = ""
    censys_api_secret: str = ""
    hibp_api_key: str = ""
    securitytrails_api_key: str = ""
    abuseipdb_api_key: str = ""
    urlscan_api_key: str = ""
    otx_api_key: str = ""
    ipinfo_token: str = ""
    numverify_api_key: str = ""

    # Cache settings
    cache_dir: str = ".osint_cache"
    cache_default_ttl: int = 3600  # seconds

    def has_key(self, provider: str) -> bool:
        """Check if an API key is configured for a provider."""
        key_field = f"{provider}_api_key"
        if key_field == "ipinfo_api_key":
            key_field = "ipinfo_token"
        value = getattr(self, key_field, "")
        return bool(value)


def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
