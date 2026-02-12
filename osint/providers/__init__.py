"""OSINT data providers."""

from osint.providers.abuseipdb import AbuseIPDBProvider
from osint.providers.hunter import HunterProvider
from osint.providers.ipinfo import IPInfoProvider
from osint.providers.numverify import NumVerifyProvider
from osint.providers.opencorporates import OpenCorporatesProvider
from osint.providers.otx import OTXProvider
from osint.providers.shodan import ShodanProvider
from osint.providers.urlscan import URLScanProvider
from osint.providers.virustotal import VirusTotalProvider

ALL_PROVIDERS = [ShodanProvider, HunterProvider, VirusTotalProvider, OTXProvider, AbuseIPDBProvider, URLScanProvider, IPInfoProvider, NumVerifyProvider, OpenCorporatesProvider]

__all__ = ["ALL_PROVIDERS", "ShodanProvider", "HunterProvider", "VirusTotalProvider", "OTXProvider", "AbuseIPDBProvider", "URLScanProvider"]
