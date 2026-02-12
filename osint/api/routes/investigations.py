"""Investigation persistence routes — CRUD, re-run, timeline, notes."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from osint.api.models import (
    AddNoteRequest,
    InvestigationCreateRequest,
    InvestigationFull,
    InvestigationSummary,
    TimelineEvent,
)
from osint.api.routes.investigate import investigate as run_investigation
from osint.api.storage import store

logger = logging.getLogger(__name__)

router = APIRouter()


def _inv_to_summary(inv: dict) -> dict:
    return {
        "id": inv["id"],
        "name": inv.get("name"),
        "subject_name": inv.get("subject_name"),
        "status": inv.get("status", "active"),
        "created_at": inv["created_at"],
        "updated_at": inv["updated_at"],
        "has_results": inv.get("results") is not None,
    }


def _inv_to_full(inv: dict) -> dict:
    return {
        "id": inv["id"],
        "name": inv.get("name"),
        "status": inv.get("status", "active"),
        "created_at": inv["created_at"],
        "updated_at": inv["updated_at"],
        "subject_name": inv.get("subject_name"),
        "aliases": inv.get("aliases") or [],
        "date_of_birth": inv.get("date_of_birth"),
        "age_range": inv.get("age_range"),
        "email": inv.get("email"),
        "phone": inv.get("phone"),
        "ip": inv.get("ip"),
        "domain": inv.get("domain"),
        "company": inv.get("company"),
        "employer": inv.get("employer"),
        "occupation": inv.get("occupation"),
        "education": inv.get("education"),
        "location": inv.get("location"),
        "address": inv.get("address"),
        "nationality": inv.get("nationality"),
        "gender": inv.get("gender"),
        "social_media": inv.get("social_media") or {},
        "vehicle": inv.get("vehicle"),
        "physical_description": inv.get("physical_description"),
        "notes": inv.get("notes"),
        "photo_ids": inv.get("photo_ids") or [],
        "results": inv.get("results"),
        "timeline": inv.get("timeline") or [],
    }


def _build_investigate_request(inv: dict) -> InvestigationCreateRequest:
    """Reconstruct an InvestigationCreateRequest from stored fields."""
    from osint.api.models import InvestigationCreateRequest

    return InvestigationCreateRequest(
        investigation_name=inv.get("name"),
        name=inv.get("subject_name"),
        email=inv.get("email"),
        phone=inv.get("phone"),
        ip=inv.get("ip"),
        domain=inv.get("domain"),
        company=inv.get("company"),
        aliases=inv.get("aliases") or [],
        date_of_birth=inv.get("date_of_birth"),
        age_range=inv.get("age_range"),
        location=inv.get("location"),
        address=inv.get("address"),
        nationality=inv.get("nationality"),
        gender=inv.get("gender"),
        employer=inv.get("employer"),
        occupation=inv.get("occupation"),
        education=inv.get("education"),
        social_media=inv.get("social_media") or {},
        vehicle=inv.get("vehicle"),
        physical_description=inv.get("physical_description"),
        notes=inv.get("notes"),
        photo_ids=inv.get("photo_ids") or [],
    )


async def _run_and_serialise(req: InvestigationCreateRequest) -> dict:
    """Run the investigation and return a JSON-serialisable dict of results."""
    from osint.api.models import InvestigateRequest

    # Create a plain InvestigateRequest (without investigation_name) for the engine
    investigate_req = InvestigateRequest(
        name=req.name,
        email=req.email,
        phone=req.phone,
        ip=req.ip,
        domain=req.domain,
        company=req.company,
        aliases=req.aliases,
        date_of_birth=req.date_of_birth,
        age_range=req.age_range,
        location=req.location,
        address=req.address,
        nationality=req.nationality,
        gender=req.gender,
        employer=req.employer,
        occupation=req.occupation,
        education=req.education,
        social_media=req.social_media,
        vehicle=req.vehicle,
        physical_description=req.physical_description,
        notes=req.notes,
        photo_ids=req.photo_ids,
    )
    response = await run_investigation(investigate_req)
    return response.model_dump(mode="json")


# ── Routes ──────────────────────────────────────────────────


@router.post("/investigations", response_model=InvestigationFull)
async def create_investigation(req: InvestigationCreateRequest) -> dict:
    """Create & run a new investigation."""
    # 1. Run the investigation
    results = await _run_and_serialise(req)

    # 2. Persist
    request_data = req.model_dump()
    inv_id = store.create(request_data, results)

    # 3. Timeline
    store.add_timeline_event(inv_id, "created", "Investigation created and initial run completed")

    # 4. Return full record
    inv = store.get(inv_id)
    if inv is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve created investigation")
    return _inv_to_full(inv)


@router.get("/investigations", response_model=list[InvestigationSummary])
async def list_investigations(
    status: str | None = Query(None),
    q: str | None = Query(None),
) -> list[dict]:
    """List / search investigations."""
    if q:
        items = store.search(q)
        if status:
            items = [i for i in items if i.get("status") == status]
    else:
        items = store.list(status=status)
    return [_inv_to_summary(i) for i in items]


@router.get("/investigations/{inv_id}", response_model=InvestigationFull)
async def get_investigation(inv_id: str) -> dict:
    """Get a full investigation with results + timeline."""
    inv = store.get(inv_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return _inv_to_full(inv)


@router.put("/investigations/{inv_id}", response_model=InvestigationFull)
async def update_investigation(inv_id: str, body: dict[str, Any]) -> dict:
    """Partial update of investigation fields (no re-run)."""
    inv = store.get(inv_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    changed: list[str] = []
    for key, value in body.items():
        old = inv.get(key)
        if old != value:
            changed.append(key)

    store.update(inv_id, body)

    if changed:
        store.add_timeline_event(
            inv_id, "updated",
            f"Fields updated: {', '.join(changed)}",
            {"changed_fields": changed},
        )

    inv = store.get(inv_id)
    return _inv_to_full(inv)  # type: ignore[arg-type]


@router.post("/investigations/{inv_id}/rerun", response_model=InvestigationFull)
async def rerun_investigation(inv_id: str) -> dict:
    """Re-run an investigation with its current fields."""
    inv = store.get(inv_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    req = _build_investigate_request(inv)
    results = await _run_and_serialise(req)

    store.save_results(inv_id, results)
    store.add_timeline_event(inv_id, "rerun", "Investigation re-run completed")

    inv = store.get(inv_id)
    return _inv_to_full(inv)  # type: ignore[arg-type]


@router.post("/investigations/{inv_id}/notes", response_model=TimelineEvent)
async def add_note(inv_id: str, body: AddNoteRequest) -> dict:
    """Add a note to the investigation timeline."""
    inv = store.get(inv_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    event_id = store.add_timeline_event(
        inv_id, "note_added", body.note,
    )
    # Fetch just-created event
    timeline = store.get_timeline(inv_id)
    event = next((e for e in timeline if e["id"] == event_id), None)
    if event is None:
        raise HTTPException(status_code=500, detail="Failed to create timeline event")
    return event


@router.delete("/investigations/{inv_id}")
async def delete_investigation(inv_id: str) -> dict:
    """Archive (soft-delete) an investigation."""
    inv = store.get(inv_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    store.delete(inv_id)
    store.add_timeline_event(inv_id, "updated", "Investigation archived")
    return {"status": "archived", "id": inv_id}


@router.get("/investigations/{inv_id}/timeline", response_model=list[TimelineEvent])
async def get_timeline(inv_id: str) -> list[dict]:
    """Get the full timeline for an investigation."""
    inv = store.get(inv_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return store.get_timeline(inv_id)
