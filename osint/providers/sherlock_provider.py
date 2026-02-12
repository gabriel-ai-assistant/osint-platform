"""Sherlock provider — username enumeration across 400+ social media sites."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from typing import Any

from osint.core.cache import Cache
from osint.core.models import ReportType, SocialProfile, UsernameReport
from osint.providers.base import BaseProvider

logger = logging.getLogger(__name__)

# Only one Sherlock instance at a time (it hammers hundreds of sites)
_semaphore = asyncio.Semaphore(1)


class SherlockProvider(BaseProvider):
    """Wraps the Sherlock CLI for username enumeration."""

    @property
    def name(self) -> str:
        return "sherlock"

    @property
    def supported_types(self) -> list[str]:
        return ["username"]

    @property
    def rate_limit_config(self) -> dict[str, Any]:
        return {"rate": 0.1, "capacity": 1}

    def __init__(self, api_key: str, cache: Cache) -> None:
        self._cache = cache
        # No API key needed — ignored

    async def lookup(self, query: str, query_type: str) -> ReportType:
        if query_type != "username":
            raise ValueError(f"Sherlock does not support query type: {query_type}")
        return await self._username_lookup(query)

    async def _username_lookup(self, username: str) -> UsernameReport:
        output_file = f"/tmp/sherlock_{uuid.uuid4().hex}.json"
        try:
            async with _semaphore:
                proc = await asyncio.create_subprocess_exec(
                    "sherlock", username,
                    "--print-found",
                    "--json", output_file,
                    "--timeout", "15",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                try:
                    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.wait()
                    logger.error("Sherlock timed out for username: %s", username)
                    return UsernameReport(
                        username=username,
                        provider=self.name,
                        raw={"error": "timeout"},
                    )

            # Parse the JSON output file
            if not os.path.exists(output_file):
                logger.warning("Sherlock output file not found: %s", output_file)
                return UsernameReport(
                    username=username,
                    provider=self.name,
                    raw={"error": "no output file", "stderr": stderr.decode(errors="replace")},
                )

            with open(output_file, "r") as f:
                raw_data = json.load(f)

            profiles: list[SocialProfile] = []
            sites_checked = 0

            # Sherlock JSON: dict of {site_name: {"url_user": ..., "status": ..., "http_status": ..., ...}}
            # or list of dicts depending on version
            if isinstance(raw_data, dict):
                for site_name, info in raw_data.items():
                    sites_checked += 1
                    if not isinstance(info, dict):
                        continue
                    # Sherlock marks found sites with status "Claimed"
                    status = info.get("status", "")
                    url = info.get("url_user", info.get("url", ""))
                    if status == "Claimed" or info.get("exists", "") == "yes":
                        profiles.append(SocialProfile(
                            platform=site_name,
                            url=url,
                            username=username,
                            exists=True,
                            extra={
                                "http_status": info.get("http_status"),
                                "response_time": info.get("response_time_s"),
                            },
                        ))
            elif isinstance(raw_data, list):
                for item in raw_data:
                    if not isinstance(item, dict):
                        continue
                    sites_checked += 1
                    site_name = item.get("site_name", item.get("name", "unknown"))
                    status = item.get("status", "")
                    url = item.get("url_user", item.get("url", ""))
                    if status == "Claimed" or item.get("exists", "") == "yes":
                        profiles.append(SocialProfile(
                            platform=site_name,
                            url=url,
                            username=username,
                            exists=True,
                            extra={
                                "http_status": item.get("http_status"),
                            },
                        ))

            return UsernameReport(
                username=username,
                provider=self.name,
                profiles_found=profiles,
                sites_checked=sites_checked,
                raw=raw_data if isinstance(raw_data, dict) else {"results": raw_data},
            )

        except json.JSONDecodeError as e:
            logger.error("Failed to parse Sherlock JSON output: %s", e)
            return UsernameReport(
                username=username,
                provider=self.name,
                raw={"error": f"JSON parse error: {e}"},
            )
        except FileNotFoundError:
            logger.error("Sherlock binary not found — is it installed?")
            return UsernameReport(
                username=username,
                provider=self.name,
                raw={"error": "sherlock not installed"},
            )
        except Exception as e:
            logger.error("Sherlock lookup failed: %s", e)
            return UsernameReport(
                username=username,
                provider=self.name,
                raw={"error": str(e)},
            )
        finally:
            # Clean up temp file
            try:
                if os.path.exists(output_file):
                    os.unlink(output_file)
            except OSError:
                pass

    async def close(self) -> None:
        """No resources to clean up."""
