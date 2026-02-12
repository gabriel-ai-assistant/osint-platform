"""Maigret provider — username enumeration across 3000+ sites with rich data."""

from __future__ import annotations

import asyncio
import glob
import json
import logging
import os
import tempfile
from typing import Any

from osint.core.cache import Cache
from osint.core.models import ReportType, SocialProfile, UsernameReport
from osint.providers.base import BaseProvider

logger = logging.getLogger(__name__)

# Only one Maigret instance at a time (very heavy — thousands of requests)
_semaphore = asyncio.Semaphore(1)

# Category mapping from Maigret tags
_TAG_CATEGORY_MAP: dict[str, str] = {
    "social": "social",
    "dating": "dating",
    "coding": "coding",
    "music": "music",
    "video": "video",
    "photo": "photo",
    "gaming": "gaming",
    "forum": "forum",
    "blog": "blog",
    "finance": "finance",
    "shopping": "shopping",
    "news": "news",
    "adult": "adult",
    "art": "art",
    "education": "education",
    "tech": "coding",
    "programming": "coding",
    "dev": "coding",
}


def _tags_to_category(tags: list[str]) -> str | None:
    """Map Maigret tags to a simplified category."""
    for tag in tags:
        tag_lower = tag.lower()
        if tag_lower in _TAG_CATEGORY_MAP:
            return _TAG_CATEGORY_MAP[tag_lower]
    return None


class MaigretProvider(BaseProvider):
    """Wraps the Maigret CLI for deep username enumeration."""

    @property
    def name(self) -> str:
        return "maigret"

    @property
    def supported_types(self) -> list[str]:
        return ["username"]

    @property
    def rate_limit_config(self) -> dict[str, Any]:
        return {"rate": 0.05, "capacity": 1}

    def __init__(self, api_key: str, cache: Cache) -> None:
        self._cache = cache

    async def lookup(self, query: str, query_type: str) -> ReportType:
        if query_type != "username":
            raise ValueError(f"Maigret does not support query type: {query_type}")
        return await self._username_lookup(query)

    async def _username_lookup(self, username: str) -> UsernameReport:
        # Maigret writes to reports/ by default; use a temp directory
        work_dir = tempfile.mkdtemp(prefix="maigret_")
        try:
            async with _semaphore:
                proc = await asyncio.create_subprocess_exec(
                    "maigret", username,
                    "--json", "flat",
                    "--no-progressbar",
                    "-n", "500",
                    "--timeout", "15",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=work_dir,
                )
                try:
                    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.wait()
                    logger.error("Maigret timed out for username: %s", username)
                    return UsernameReport(
                        username=username,
                        provider=self.name,
                        raw={"error": "timeout"},
                    )

            # Find the output JSON — Maigret writes to reports/ subdir
            json_files = glob.glob(os.path.join(work_dir, "reports", "*.json"))
            if not json_files:
                # Also check working dir root
                json_files = glob.glob(os.path.join(work_dir, "*.json"))

            if not json_files:
                logger.warning("Maigret produced no JSON output for: %s", username)
                return UsernameReport(
                    username=username,
                    provider=self.name,
                    raw={
                        "error": "no output file",
                        "stderr": stderr.decode(errors="replace")[:2000],
                        "stdout": stdout.decode(errors="replace")[:2000],
                    },
                )

            # Read the first JSON file found
            with open(json_files[0], "r") as f:
                raw_data = json.load(f)

            profiles: list[SocialProfile] = []
            sites_checked = 0

            # Maigret flat JSON: list of dicts with {sitename, url_user, status, tags[], ...}
            items = raw_data if isinstance(raw_data, list) else raw_data.get("results", [])

            for item in items:
                if not isinstance(item, dict):
                    continue
                sites_checked += 1
                status = str(item.get("status", "")).lower()
                # "claimed" means the username exists on the site
                if status in ("claimed", "found"):
                    site_name = item.get("sitename", item.get("site_name", item.get("name", "unknown")))
                    url = item.get("url_user", item.get("url", ""))
                    tags = item.get("tags", [])
                    if isinstance(tags, str):
                        tags = [t.strip() for t in tags.split(",")]

                    profiles.append(SocialProfile(
                        platform=site_name,
                        url=url,
                        username=username,
                        exists=True,
                        category=_tags_to_category(tags),
                        extra={
                            "tags": tags,
                            "http_status": item.get("http_status"),
                            "response_time": item.get("response_time_s"),
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
            logger.error("Failed to parse Maigret JSON output: %s", e)
            return UsernameReport(
                username=username,
                provider=self.name,
                raw={"error": f"JSON parse error: {e}"},
            )
        except FileNotFoundError:
            logger.error("Maigret binary not found — is it installed?")
            return UsernameReport(
                username=username,
                provider=self.name,
                raw={"error": "maigret not installed"},
            )
        except Exception as e:
            logger.error("Maigret lookup failed: %s", e)
            return UsernameReport(
                username=username,
                provider=self.name,
                raw={"error": str(e)},
            )
        finally:
            # Clean up temp directory
            try:
                import shutil
                shutil.rmtree(work_dir, ignore_errors=True)
            except Exception:
                pass

    async def close(self) -> None:
        """No resources to clean up."""
