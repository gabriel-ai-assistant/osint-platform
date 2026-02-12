"""Single-query lookup endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from osint.aggregator import aggregate, detect_query_type
from osint.api.models import LookupRequest, LookupResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/lookup", response_model=LookupResponse)
async def lookup(req: LookupRequest) -> LookupResponse:
    """Perform a single-query lookup across all applicable providers."""
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    query_type = req.query_type or detect_query_type(query)
    if query_type == "unknown":
        raise HTTPException(
            status_code=400,
            detail=f"Could not detect query type for: {query}. Please specify query_type.",
        )

    try:
        report = await aggregate(query=query, query_type=query_type)
    except Exception as e:
        logger.exception("Lookup failed for %s (%s)", query, query_type)
        raise HTTPException(status_code=500, detail=str(e))

    # Convert report objects to dicts for JSON response
    report_dicts = []
    for r in report.reports:
        report_dicts.append(r.model_dump(mode="json"))

    return LookupResponse(
        query=report.query,
        query_type=report.query_type,
        reports=report_dicts,
        confidence=report.confidence,
        providers_queried=report.providers_queried,
        providers_failed=report.providers_failed,
        timestamp=report.timestamp,
    )
