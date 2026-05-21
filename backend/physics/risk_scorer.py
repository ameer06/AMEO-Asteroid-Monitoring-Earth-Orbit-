"""
Composite risk scoring for Near-Earth Objects.

Score is a value in [0, 100] representing relative hazard.
"""

import math

# LD in km
LD_KM = 384_402.0

RISK_TIERS = [
    (75.0, "CRITICAL"),
    (50.0, "HIGH"),
    (25.0, "MEDIUM"),
    (0.0,  "LOW"),
]


def compute_risk_score(
    miss_distance_km: float,
    diameter_km: float,
    velocity_kmps: float,
    uncertainty_km: float = 0.0,
) -> float:
    """
    Composite risk score in [0, 100].

    Components (each normalised to [0, 1]):
      - Proximity factor:   closer → higher risk (exponential decay)
      - Size factor:        larger diameter → higher risk (log scale)
      - Velocity factor:    faster → higher risk (log scale)
      - Uncertainty factor: higher uncertainty → higher risk
    """
    # 1. Proximity (miss distance in LD)
    miss_ld = miss_distance_km / LD_KM
    prox = math.exp(-miss_ld / 10.0)  # max=1 at 0 LD, ~0 at 100 LD

    # 2. Size (diameter 0–10 km scale)
    size = min(1.0, math.log1p(max(0.0, diameter_km)) / math.log1p(10.0))

    # 3. Velocity (0–30 km/s scale)
    vel = min(1.0, math.log1p(max(0.0, velocity_kmps)) / math.log1p(30.0))

    # 4. Uncertainty amplifier (0 → 1 over 1 LD of uncertainty)
    uncert = min(1.0, uncertainty_km / LD_KM)

    # Weighted combination
    score = (0.45 * prox + 0.25 * size + 0.20 * vel + 0.10 * uncert) * 100.0
    return round(min(100.0, max(0.0, score)), 2)


def risk_tier(score: float) -> str:
    for threshold, label in RISK_TIERS:
        if score >= threshold:
            return label
    return "LOW"


def score_neo(
    miss_distance_km: float,
    diameter_min_km: float,
    diameter_max_km: float,
    velocity_kmps: float,
    uncertainty_km: float = 0.0,
) -> dict:
    """Score using mean diameter and return full result dict."""
    diameter_km = (diameter_min_km + diameter_max_km) / 2.0
    score = compute_risk_score(miss_distance_km, diameter_km, velocity_kmps, uncertainty_km)
    return {
        "score": score,
        "tier": risk_tier(score),
        "components": {
            "proximity": round(math.exp(-miss_distance_km / LD_KM / 10.0), 4),
            "size": round(min(1.0, math.log1p(diameter_km) / math.log1p(10.0)), 4),
            "velocity": round(min(1.0, math.log1p(velocity_kmps) / math.log1p(30.0)), 4),
            "uncertainty": round(min(1.0, uncertainty_km / LD_KM), 4),
        },
    }
