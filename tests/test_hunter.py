"""Tests for the Hunter provider and related models."""

from __future__ import annotations

from osint.core.models import DomainReport, EmailContact, EmailReport


class TestDomainReport:
    def test_with_emails(self):
        report = DomainReport(
            domain="example.com",
            provider="hunter",
            organization="Example Inc",
            emails=[
                EmailContact(email="ceo@example.com", confidence=95),
                EmailContact(email="info@example.com", confidence=80),
            ],
        )
        assert len(report.emails) == 2
        assert report.emails[0].confidence == 95


class TestEmailReport:
    def test_create(self):
        report = EmailReport(
            email="test@example.com",
            provider="hunter",
            deliverable=True,
            disposable=False,
            confidence=92,
        )
        assert report.deliverable is True
        assert report.confidence == 92
