"""
REST endpoints for NEO data.

GET /neos               — paginated list with filters
GET /neos/{id}          — single NEO detail
GET /neos/{id}/orbit    — orbital elements + propagated path
GET /neos/{id}/montecarlo — Monte Carlo uncertainty corridor
GET /neos/{id}/history  — historical close approaches
GET /alerts/log         — persisted alert log
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.services import neo_service

router = APIRouter(prefix="/neos", tags=["NEOs"])


@router.get("")
async def list_neos(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    hazardous_only: bool = Query(False),
    sort_by: str = Query("risk_score", regex="^(risk_score|name|estimated_diameter_max_km)$"),
    sort_dir: str = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    """Paginated, filterable NEO list sorted by chosen field."""
    return await neo_service.list_neos(
        db, page=page, limit=limit,
        hazardous_only=hazardous_only,
        sort_by=sort_by, sort_dir=sort_dir,
    )


@router.get("/{neo_id}")
async def get_neo(neo_id: str, db: AsyncSession = Depends(get_db)):
    """Full detail for a single NEO."""
    neo = await neo_service.get_neo_detail(db, neo_id)
    if not neo:
        raise HTTPException(status_code=404, detail=f"NEO {neo_id} not found")
    return neo


@router.get("/{neo_id}/orbit")
async def get_orbit(neo_id: str, db: AsyncSession = Depends(get_db)):
    """Keplerian elements and RK4-propagated orbit path (30-day window)."""
    neo = await neo_service.get_neo(db, neo_id)
    if not neo:
        raise HTTPException(status_code=404, detail=f"NEO {neo_id} not found")
    return await neo_service.get_orbit_data(neo)


@router.get("/{neo_id}/montecarlo")
async def get_montecarlo(neo_id: str, db: AsyncSession = Depends(get_db)):
    """Monte Carlo uncertainty corridor (N=500 runs, position + velocity perturbations)."""
    neo = await neo_service.get_neo(db, neo_id)
    if not neo:
        raise HTTPException(status_code=404, detail=f"NEO {neo_id} not found")
    return await neo_service.get_montecarlo_data(neo)


@router.get("/{neo_id}/history")
async def get_history(
    neo_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Historical and upcoming close approach records for this NEO."""
    neo = await neo_service.get_neo(db, neo_id)
    if not neo:
        raise HTTPException(status_code=404, detail=f"NEO {neo_id} not found")
    return await neo_service.get_neo_history(db, neo_id, limit=limit)
