"""OSINT data providers."""

from osint.providers.hunter import HunterProvider
from osint.providers.otx import OTXProvider
from osint.providers.shodan import ShodanProvider
from osint.providers.virustotal import VirusTotalProvider

ALL_PROVIDERS = [ShodanProvider, HunterProvider, VirusTotalProvider, OTXProvider]

__all__ = ["ALL_PROVIDERS", "ShodanProvider", "HunterProvider", "VirusTotalProvider", "OTXProvider"]
