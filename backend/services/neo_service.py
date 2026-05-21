"""
NEO service layer — business logic between routes and DB/physics.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.neo import NEO, CloseApproach, AlertLog
from backend.services.nasa_client import (
    fetch_neo_detail,
    fetch_neows_feed,
    parse_neows_objects,
)
from backend.physics.orbital_mechanics import (
    propagate_orbit, monte_carlo_approach, closest_approach
)
from backend.physics.risk_scorer import score_neo
from backend.config import get_settings

settings = get_settings()
LD_KM = 384_402.0


# ── Ingest ────────────────────────────────────────────────────────────────────

async def ingest_neows(db: AsyncSession) -> List[str]:
    """
    Pull latest NeoWs feed, upsert NEOs & close approaches.
    Returns list of neo_ids that breach the alert threshold.
    """
    raw = await fetch_neows_feed()
    objects = parse_neows_objects(raw)
    alert_ids: List[str] = []

    for obj in objects:
        # Upsert NEO master record
        neo = await db.get(NEO, obj["id"])
        if neo is None:
            neo = NEO(id=obj["id"])
            db.add(neo)

        neo.name = obj["name"]
        neo.designation = obj["designation"]
        neo.is_potentially_hazardous = obj["is_potentially_hazardous"]
        neo.absolute_magnitude = obj["absolute_magnitude"]
        neo.estimated_diameter_min_km = obj["estimated_diameter_min_km"]
        neo.estimated_diameter_max_km = obj["estimated_diameter_max_km"]
        neo.nasa_jpl_url = obj["nasa_jpl_url"]
        _apply_orbital_elements(neo, obj)

        if not _has_orbital_elements(neo):
            try:
                detail = await fetch_neo_detail(obj["id"])
                _apply_orbital_elements(neo, _extract_orbital_elements(detail))
            except Exception:
                # NeoWs feed data is still useful even when the detail lookup is rate-limited
                # or missing orbital metadata for a specific object.
                pass

        # Score
        scored = score_neo(
            miss_distance_km=obj["miss_distance_km"],
            diameter_min_km=obj["estimated_diameter_min_km"],
            diameter_max_km=obj["estimated_diameter_max_km"],
            velocity_kmps=obj["relative_velocity_kmps"],
        )
        neo.risk_score = scored["score"]
        neo.risk_tier = scored["tier"]

        # Upsert close approach
        if obj["approach_date"]:
            try:
                approach_dt = datetime.strptime(obj["approach_date"], "%Y-%m-%d")
            except ValueError:
                approach_dt = datetime.utcnow()

            approach = CloseApproach(
                neo_id=neo.id,
                approach_date=approach_dt,
                miss_distance_km=obj["miss_distance_km"],
                miss_distance_ld=obj["miss_distance_ld"],
                relative_velocity_kmps=obj["relative_velocity_kmps"],
            )
            db.add(approach)

            # Check alert threshold
            if obj["miss_distance_ld"] < settings.alert_threshold_ld:
                alert_ids.append(neo.id)

    await db.flush()
    return alert_ids


# ── Query helpers ─────────────────────────────────────────────────────────────

async def list_neos(
    db: AsyncSession,
    page: int = 1,
    limit: int = 20,
    hazardous_only: bool = False,
    sort_by: str = "risk_score",
    sort_dir: str = "desc",
) -> Dict[str, Any]:
    query = select(NEO)
    count_query = select(func.count()).select_from(NEO)
    if hazardous_only:
        query = query.where(NEO.is_potentially_hazardous == True)  # noqa: E712
        count_query = count_query.where(NEO.is_potentially_hazardous == True)  # noqa: E712

    order_col = getattr(NEO, sort_by, NEO.risk_score)
    if sort_dir == "desc":
        query = query.order_by(desc(order_col))
    else:
        query = query.order_by(order_col)

    total = await db.scalar(count_query) or 0

    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    neos = result.scalars().all()
    latest_by_neo_id = await _latest_approaches_for_neos(db, [n.id for n in neos])

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": [_neo_to_dict(n, latest_by_neo_id.get(n.id)) for n in neos],
    }


async def get_neo(db: AsyncSession, neo_id: str) -> Optional[NEO]:
    return await db.get(NEO, neo_id)


async def get_neo_detail(db: AsyncSession, neo_id: str) -> Optional[Dict[str, Any]]:
    neo = await get_neo(db, neo_id)
    if not neo:
        return None
    latest = await _latest_approaches_for_neos(db, [neo_id])
    return _neo_to_dict(neo, latest.get(neo_id))


async def get_neo_history(
    db: AsyncSession, neo_id: str, limit: int = 50
) -> List[Dict[str, Any]]:
    result = await db.execute(
        select(CloseApproach)
        .where(CloseApproach.neo_id == neo_id)
        .order_by(desc(CloseApproach.approach_date))
        .limit(limit)
    )
    approaches = result.scalars().all()
    return [
        {
            "approach_date": a.approach_date.isoformat(),
            "miss_distance_km": a.miss_distance_km,
            "miss_distance_ld": a.miss_distance_ld,
            "relative_velocity_kmps": a.relative_velocity_kmps,
            "uncertainty_plus_km": a.uncertainty_plus_km,
            "uncertainty_minus_km": a.uncertainty_minus_km,
        }
        for a in approaches
    ]


async def get_orbit_data(neo: NEO) -> Dict[str, Any]:
    """Propagate orbit and return path points."""
    if not _has_orbital_elements(neo):
        return {"error": "No orbital elements available for this NEO"}

    path = propagate_orbit(
        a=neo.semi_major_axis,
        e=neo.eccentricity,
        i=neo.inclination,
        raan=neo.raan,
        argp=neo.arg_perihelion,
        M=neo.mean_anomaly,
        days=30.0,
        steps=300,
    )
    approach = closest_approach(
        a=neo.semi_major_axis,
        e=neo.eccentricity,
        i=neo.inclination,
        raan=neo.raan,
        argp=neo.arg_perihelion,
        M=neo.mean_anomaly,
    )
    return {
        "neo_id": neo.id,
        "elements": {
            "a": neo.semi_major_axis,
            "e": neo.eccentricity,
            "i": neo.inclination,
            "raan": neo.raan,
            "argp": neo.arg_perihelion,
            "M": neo.mean_anomaly,
        },
        "path": path,
        "closest_approach": approach,
    }


async def get_montecarlo_data(neo: NEO) -> Dict[str, Any]:
    """Run Monte Carlo simulation for uncertainty corridor."""
    if not _has_orbital_elements(neo):
        return {"error": "No orbital elements available for this NEO"}

    result = monte_carlo_approach(
        a=neo.semi_major_axis,
        e=neo.eccentricity,
        i=neo.inclination,
        raan=neo.raan,
        argp=neo.arg_perihelion,
        M=neo.mean_anomaly,
        n_runs=500,  # reduced for API response speed; tests use 1000
    )
    return {"neo_id": neo.id, **result}


async def get_alert_log(db: AsyncSession, limit: int = 50) -> List[Dict[str, Any]]:
    result = await db.execute(
        select(AlertLog).order_by(desc(AlertLog.triggered_at)).limit(limit)
    )
    logs = result.scalars().all()
    return [
        {
            "id": l.id,
            "neo_id": l.neo_id,
            "neo_name": l.neo_name,
            "miss_distance_ld": l.miss_distance_ld,
            "approach_date": l.approach_date,
            "triggered_at": l.triggered_at.isoformat(),
        }
        for l in logs
    ]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _has_orbital_elements(neo: NEO) -> bool:
    return all(
        v is not None
        for v in [
            neo.semi_major_axis, neo.eccentricity, neo.inclination,
            neo.raan, neo.arg_perihelion, neo.mean_anomaly,
        ]
    )


async def _latest_approaches_for_neos(
    db: AsyncSession,
    neo_ids: List[str],
) -> Dict[str, CloseApproach]:
    if not neo_ids:
        return {}

    result = await db.execute(
        select(CloseApproach)
        .where(CloseApproach.neo_id.in_(neo_ids))
        .order_by(CloseApproach.neo_id, desc(CloseApproach.approach_date))
    )

    latest: Dict[str, CloseApproach] = {}
    for approach in result.scalars().all():
        latest.setdefault(approach.neo_id, approach)
    return latest


def _neo_to_dict(
    neo: NEO,
    latest_approach: Optional[CloseApproach] = None,
) -> Dict[str, Any]:
    data = {
        "id": neo.id,
        "name": neo.name,
        "designation": neo.designation,
        "is_potentially_hazardous": neo.is_potentially_hazardous,
        "absolute_magnitude": neo.absolute_magnitude,
        "estimated_diameter_min_km": neo.estimated_diameter_min_km,
        "estimated_diameter_max_km": neo.estimated_diameter_max_km,
        "nasa_jpl_url": neo.nasa_jpl_url,
        "risk_score": neo.risk_score,
        "risk_tier": neo.risk_tier,
        "updated_at": neo.updated_at.isoformat() if neo.updated_at else None,
    }
    if latest_approach:
        data.update({
            "approach_date": latest_approach.approach_date.isoformat(),
            "miss_distance_km": latest_approach.miss_distance_km,
            "miss_distance_ld": latest_approach.miss_distance_ld,
            "relative_velocity_kmps": latest_approach.relative_velocity_kmps,
        })
    return data


def _extract_orbital_elements(payload: Dict[str, Any]) -> Dict[str, Any]:
    orbital = payload.get("orbital_data") or {}
    return {
        "semi_major_axis": orbital.get("semi_major_axis"),
        "eccentricity": orbital.get("eccentricity"),
        "inclination": orbital.get("inclination"),
        "raan": orbital.get("ascending_node_longitude"),
        "arg_perihelion": orbital.get("perihelion_argument"),
        "mean_anomaly": orbital.get("mean_anomaly"),
    }


def _apply_orbital_elements(neo: NEO, data: Dict[str, Any]) -> None:
    element_map = {
        "semi_major_axis": "semi_major_axis",
        "eccentricity": "eccentricity",
        "inclination": "inclination",
        "raan": "raan",
        "arg_perihelion": "arg_perihelion",
        "mean_anomaly": "mean_anomaly",
    }
    for source_key, attr in element_map.items():
        value = data.get(source_key)
        if value is None or value == "":
            continue
        try:
            setattr(neo, attr, float(value))
        except (TypeError, ValueError):
            continue
