"""OSINT data providers."""

from osint.providers.hunter import HunterProvider
from osint.providers.shodan import ShodanProvider

ALL_PROVIDERS = [ShodanProvider, HunterProvider]

__all__ = ["ALL_PROVIDERS", "ShodanProvider", "HunterProvider"]
