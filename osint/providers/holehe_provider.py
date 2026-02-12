"""Holehe provider — discover which services an email is registered on."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

from osint.core.cache import Cache
from osint.core.models import EmailAccountsReport, ReportType
from osint.providers.base import BaseProvider

logger = logging.getLogger(__name__)

# Only one Holehe instance at a time
_semaphore = asyncio.Semaphore(1)


class HoleheProvider(BaseProvider):
    """Wraps the Holehe CLI for email account discovery."""

    @property
    def name(self) -> str:
        return "holehe"

    @property
    def supported_types(self) -> list[str]:
        return ["email"]

    @property
    def rate_limit_config(self) -> dict[str, Any]:
        return {"rate": 0.1, "capacity": 1}

    def __init__(self, api_key: str, cache: Cache) -> None:
        self._cache = cache

    async def lookup(self, query: str, query_type: str) -> ReportType:
        if query_type != "email":
            raise ValueError(f"Holehe does not support query type: {query_type}")
        return await self._email_lookup(query)

    async def _email_lookup(self, email: str) -> EmailAccountsReport:
        try:
            async with _semaphore:
                proc = await asyncio.create_subprocess_exec(
                    "holehe", email,
                    "--no-color",
                    "--only-used",
                    "--no-clear",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                try:
                    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.wait()
                    logger.error("Holehe timed out for email: %s", email)
                    return EmailAccountsReport(
                        email=email,
                        provider=self.name,
                        raw={"error": "timeout"},
                    )

            output = stdout.decode(errors="replace")
            stderr_text = stderr.decode(errors="replace")

            registered: list[str] = []
            not_found: list[str] = []
            total_checked = 0

            for line in output.splitlines():
                line = line.strip()
                if not line:
                    continue

                # Holehe output format:
                # [+] service.com — registered
                # [-] service.com — not found
                # [x] service.com — rate limited / error
                found_match = re.match(r"\[\+\]\s*(.+?)(?:\s*[-—]|$)", line)
                if found_match:
                    service = found_match.group(1).strip()
                    if service:
                        registered.append(service)
                        total_checked += 1
                    continue

                not_found_match = re.match(r"\[-\]\s*(.+?)(?:\s*[-—]|$)", line)
                if not_found_match:
                    service = not_found_match.group(1).strip()
                    if service:
                        not_found.append(service)
                        total_checked += 1
                    continue

                # Also count [x] lines as checked
                error_match = re.match(r"\[x\]\s*(.+?)(?:\s*[-—]|$)", line)
                if error_match:
                    total_checked += 1

            return EmailAccountsReport(
                email=email,
                provider=self.name,
                registered_services=registered,
                not_found_services=not_found,
                total_checked=total_checked,
                raw={
                    "stdout": output[:5000],
                    "stderr": stderr_text[:2000],
                    "return_code": proc.returncode,
                },
            )

        except FileNotFoundError:
            logger.error("Holehe binary not found — is it installed?")
            return EmailAccountsReport(
                email=email,
                provider=self.name,
                raw={"error": "holehe not installed"},
            )
        except Exception as e:
            logger.error("Holehe lookup failed: %s", e)
            return EmailAccountsReport(
                email=email,
                provider=self.name,
                raw={"error": str(e)},
            )

    async def close(self) -> None:
        """No resources to clean up."""
