"""Tests for the Shodan provider."""

from __future__ import annotations

from osint.aggregator import detect_query_type
from osint.core.models import IPReport, GeoLocation, PortInfo


class TestQueryDetection:
    def test_ip(self):
        assert detect_query_type("8.8.8.8") == "ip"

    def test_domain(self):
        assert detect_query_type("example.com") == "domain"

    def test_email(self):
        assert detect_query_type("user@example.com") == "email"

    def test_url(self):
        assert detect_query_type("https://example.com/path") == "url"


class TestIPReport:
    def test_create(self):
        report = IPReport(
            ip="1.1.1.1",
            provider="shodan",
            hostnames=["one.one.one.one"],
            ports=[PortInfo(port=80, protocol="tcp", service="http")],
            geo=GeoLocation(country="US", city="Los Angeles"),
        )
        assert report.ip == "1.1.1.1"
        assert len(report.ports) == 1
        assert report.geo.country == "US"
