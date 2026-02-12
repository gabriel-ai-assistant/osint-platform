"""CLI entry point for the OSINT platform."""

from __future__ import annotations

import asyncio

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from osint.aggregator import aggregate, detect_query_type
from osint.config import get_settings
from osint.core.models import (
    AggregatedReport,
    DomainReport,
    EmailReport,
    IPReport,
)
from osint.providers.numverify import PhoneReport
from osint.providers.opencorporates import CompanyReport
from osint.providers import ALL_PROVIDERS

console = Console()

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


def _render_report(report: AggregatedReport) -> None:
    """Render an aggregated report with Rich."""
    console.print()
    console.print(
        Panel(
            f"[bold]{report.query}[/bold]  •  type: {report.query_type}  •  "
            f"confidence: {report.confidence:.0%}",
            title="OSINT Report",
            border_style="blue",
        )
    )

    if report.providers_failed:
        console.print(f"[yellow]⚠ Failed providers: {', '.join(report.providers_failed)}[/yellow]")

    for r in report.reports:
        console.print()
        if isinstance(r, IPReport):
            _render_ip(r)
        elif isinstance(r, DomainReport):
            _render_domain(r)
        elif isinstance(r, EmailReport):
            _render_email(r)
        elif isinstance(r, PhoneReport):
            _render_phone(r)
        elif isinstance(r, CompanyReport):
            _render_company(r)
        else:
            console.print(f"[dim]{r.provider}: {r}[/dim]")

    if not report.reports:
        console.print("[red]No results found.[/red]")


def _render_ip(r: IPReport) -> None:
    table = Table(title=f"IP Report — {r.provider}", show_lines=True)
    table.add_column("Field", style="cyan")
    table.add_column("Value")

    table.add_row("IP", r.ip)
    table.add_row("Hostnames", ", ".join(r.hostnames) or "—")
    table.add_row("OS", r.os or "—")

    if r.geo:
        geo_str = f"{r.geo.city or '?'}, {r.geo.country or '?'} ({r.geo.org or '?'})"
        table.add_row("Location", geo_str)

    if r.ports:
        ports_str = ", ".join(f"{p.port}/{p.protocol}" for p in r.ports[:20])
        table.add_row("Ports", ports_str)

    if r.vulns:
        table.add_row("Vulns", ", ".join(v.cve_id for v in r.vulns[:10]))

    console.print(table)


def _render_domain(r: DomainReport) -> None:
    table = Table(title=f"Domain Report — {r.provider}", show_lines=True)
    table.add_column("Field", style="cyan")
    table.add_column("Value")

    table.add_row("Domain", r.domain)
    table.add_row("Organization", r.organization or "—")

    if r.emails:
        emails_str = "\n".join(
            f"{e.email} ({e.confidence}%)" for e in r.emails[:10]
        )
        table.add_row("Emails", emails_str)

    if r.dns_records:
        dns_str = "\n".join(f"{k}: {', '.join(v)}" for k, v in r.dns_records.items())
        table.add_row("DNS", dns_str)

    if r.technologies:
        table.add_row("Technologies", ", ".join(r.technologies))

    console.print(table)


def _render_email(r: EmailReport) -> None:
    table = Table(title=f"Email Report — {r.provider}", show_lines=True)
    table.add_column("Field", style="cyan")
    table.add_column("Value")

    table.add_row("Email", r.email)
    table.add_row("Deliverable", str(r.deliverable) if r.deliverable is not None else "—")
    table.add_row("Disposable", str(r.disposable) if r.disposable is not None else "—")
    table.add_row("Confidence", f"{r.confidence}%" if r.confidence else "—")

    name = f"{r.first_name or ''} {r.last_name or ''}".strip()
    if name:
        table.add_row("Name", name)
    if r.organization:
        table.add_row("Organization", r.organization)

    console.print(table)


def _render_phone(r: PhoneReport) -> None:
    table = Table(title=f"Phone Report — {r.provider}", show_lines=True)
    table.add_column("Field", style="cyan")
    table.add_column("Value")

    table.add_row("Phone", r.phone)
    table.add_row("Valid", str(r.valid) if r.valid is not None else "—")
    table.add_row("International", r.international_format or "—")
    table.add_row("Local", r.local_format or "—")
    table.add_row("Country", f"{r.country_name or '?'} (+{r.country_prefix or '?'})")
    table.add_row("Location", r.location or "—")
    table.add_row("Carrier", r.carrier or "—")
    table.add_row("Line Type", r.line_type or "—")

    console.print(table)


def _render_company(r: CompanyReport) -> None:
    table = Table(title=f"Company Report — {r.provider} ({r.total_results} total)", show_lines=True)
    table.add_column("Name", style="cyan")
    table.add_column("Jurisdiction")
    table.add_column("Status")
    table.add_column("Incorporated")
    table.add_column("Address")

    for c in r.companies[:10]:
        table.add_row(
            c.get("name", "—"),
            c.get("jurisdiction", "—"),
            c.get("status", "—"),
            c.get("incorporation_date", "—"),
            (c.get("registered_address") or "—")[:60],
        )

    console.print(table)


@click.group()
def cli() -> None:
    """OSINT Platform — multi-source intelligence aggregation."""


@cli.command()
@click.argument("query")
def lookup(query: str) -> None:
    """Auto-detect query type and look up across all providers."""
    qtype = detect_query_type(query)
    console.print(f"[dim]Detected query type: {qtype}[/dim]")
    report = asyncio.run(aggregate(query, qtype))
    _render_report(report)


@cli.command()
@click.argument("ip")
def ip(ip: str) -> None:
    """Look up an IP address."""
    report = asyncio.run(aggregate(ip, "ip"))
    _render_report(report)


@cli.command()
@click.argument("domain")
def domain(domain: str) -> None:
    """Look up a domain."""
    report = asyncio.run(aggregate(domain, "domain"))
    _render_report(report)


@cli.command()
@click.argument("email")
def email(email: str) -> None:
    """Look up an email address."""
    report = asyncio.run(aggregate(email, "email"))
    _render_report(report)


@cli.command()
@click.argument("number")
def phone(number: str) -> None:
    """Look up a phone number."""
    report = asyncio.run(aggregate(number, "phone"))
    _render_report(report)


@cli.command()
@click.argument("name")
def company(name: str) -> None:
    """Look up a company."""
    report = asyncio.run(aggregate(name, "company"))
    _render_report(report)


@cli.command()
def providers() -> None:
    """List configured providers and their status."""
    settings = get_settings()
    table = Table(title="OSINT Providers")
    table.add_column("Provider", style="cyan")
    table.add_column("Types")
    table.add_column("Status")

    for cls in ALL_PROVIDERS:
        name = cls.__name__.replace("Provider", "").lower()
        # Temp instance to get metadata
        key_attr = _KEY_MAP.get(name, f"{name}_api_key")
        if key_attr is None:
            status = "[green]✓ no key needed[/green]"
        else:
            api_key = getattr(settings, key_attr, "")
            status = "[green]✓ configured[/green]" if api_key else "[red]✗ no key[/red]"
        # Get supported types from class
        dummy_types = cls.__dict__.get("supported_types", property())
        try:
            types_list = cls.supported_types.fget(None)  # type: ignore
        except Exception:
            types_list = ["?"]
        table.add_row(name.capitalize(), ", ".join(types_list), status)

    console.print(table)


if __name__ == "__main__":
    cli()
