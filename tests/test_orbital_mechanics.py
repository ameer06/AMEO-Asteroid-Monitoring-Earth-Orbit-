"""
pytest unit tests for the custom orbital mechanics engine.

Run with:  pytest tests/ -v
"""

import math
import pytest

from backend.physics.orbital_mechanics import (
    keplerian_to_state,
    state_to_keplerian,
    propagate_orbit,
    monte_carlo_approach,
    closest_approach,
    AU, LD,
)
from backend.physics.risk_scorer import compute_risk_score, risk_tier, score_neo


# ─── Fixtures ──────────────────────────────────────────────────────────────────

# Earth's approximate orbital elements
EARTH_ELEMENTS = dict(a=1.0, e=0.0167, i=0.0, raan=0.0, argp=102.9, M=0.0)

# Apophis 99942 — classic test case
APOPHIS_ELEMENTS = dict(a=0.9224, e=0.1912, i=3.331, raan=204.46, argp=126.39, M=222.45)


# ─── Keplerian ↔ State round-trip ──────────────────────────────────────────────

def test_keplerian_to_state_earth_distance():
    """Earth at 1 AU should produce |r| ≈ 1 AU."""
    r, v = keplerian_to_state(**EARTH_ELEMENTS)
    r_au = math.sqrt(sum(x**2 for x in r)) / AU
    assert abs(r_au - 1.0) < 0.02, f"Expected ~1 AU, got {r_au}"


def test_state_to_keplerian_round_trip():
    """Convert Earth to state and back — elements should be ~identical."""
    r, v = keplerian_to_state(**EARTH_ELEMENTS)
    recovered = state_to_keplerian(r, v)
    assert abs(recovered['a'] - EARTH_ELEMENTS['a']) < 1e-4, "Semi-major axis mismatch"
    assert abs(recovered['e'] - EARTH_ELEMENTS['e']) < 1e-4, "Eccentricity mismatch"


def test_keplerian_velocity_magnitude():
    """Earth's orbital velocity at perihelion should be ~30.3 km/s."""
    r, v = keplerian_to_state(**EARTH_ELEMENTS)
    v_kmps = math.sqrt(sum(x**2 for x in v)) / 1000.0
    assert 29.0 < v_kmps < 31.0, f"Expected ~30 km/s, got {v_kmps}"


def test_apophis_semimajor_axis():
    """Apophis orbit should have a < 1 AU (inner NEO)."""
    r, v = keplerian_to_state(**APOPHIS_ELEMENTS)
    recovered = state_to_keplerian(r, v)
    assert recovered['a'] < 1.0


# ─── RK4 Propagator ────────────────────────────────────────────────────────────

def test_propagate_orbit_returns_points():
    """Propagation should return exactly steps+1 points."""
    path = propagate_orbit(**EARTH_ELEMENTS, days=30.0, steps=100)
    assert len(path) == 101


def test_propagate_orbit_conserves_distance():
    """
    Circular orbit: |r| should stay ~constant throughout propagation.
    """
    circular = dict(a=1.0, e=0.0, i=0.0, raan=0.0, argp=0.0, M=0.0)
    path = propagate_orbit(**circular, days=365.0, steps=500)
    distances = [math.sqrt(p['x']**2 + p['y']**2 + p['z']**2) for p in path]
    r_min, r_max = min(distances), max(distances)
    # Should stay within 1% of 1 AU
    assert abs(r_min - 1.0) < 0.01, f"r_min deviated: {r_min}"
    assert abs(r_max - 1.0) < 0.01, f"r_max deviated: {r_max}"


def test_propagate_orbit_structure():
    """Each path point must have t, x, y, z keys."""
    path = propagate_orbit(**EARTH_ELEMENTS, days=5.0, steps=50)
    for p in path:
        assert 't' in p
        assert 'x' in p
        assert 'y' in p
        assert 'z' in p
        assert 0.0 <= p['t'] <= 5.0


# ─── Monte Carlo ───────────────────────────────────────────────────────────────

def test_monte_carlo_returns_expected_keys():
    result = monte_carlo_approach(**EARTH_ELEMENTS, n_runs=50, days=10.0)
    for key in ['mean_miss_km', 'std_miss_km', 'p05_miss_km', 'p95_miss_km', 'mean_miss_ld', 'corridor']:
        assert key in result, f"Missing key: {key}"


def test_monte_carlo_std_positive():
    result = monte_carlo_approach(**EARTH_ELEMENTS, n_runs=100, sigma_r_km=500.0, days=10.0)
    assert result['std_miss_km'] >= 0


def test_monte_carlo_percentile_order():
    result = monte_carlo_approach(**EARTH_ELEMENTS, n_runs=100, days=10.0)
    assert result['p05_miss_km'] <= result['mean_miss_km'] <= result['p95_miss_km']


# ─── Risk Scoring ──────────────────────────────────────────────────────────────

def test_risk_score_range():
    score = compute_risk_score(
        miss_distance_km=100_000,
        diameter_km=0.5,
        velocity_kmps=10.0,
    )
    assert 0.0 <= score <= 100.0


def test_risk_score_closer_is_higher():
    close = compute_risk_score(50_000, 1.0, 15.0)
    far   = compute_risk_score(5_000_000, 1.0, 15.0)
    assert close > far, "Closer approach should yield higher risk score"


def test_risk_score_larger_is_higher():
    small = compute_risk_score(500_000, 0.01, 10.0)
    large = compute_risk_score(500_000, 5.0,  10.0)
    assert large > small


def test_risk_tier_critical():
    assert risk_tier(80.0) == 'CRITICAL'


def test_risk_tier_low():
    assert risk_tier(10.0) == 'LOW'


def test_score_neo_returns_dict():
    result = score_neo(
        miss_distance_km=384_402.0,  # 1 LD
        diameter_min_km=0.1,
        diameter_max_km=0.3,
        velocity_kmps=20.0,
    )
    assert 'score' in result
    assert 'tier' in result
    assert 'components' in result


# ─── Closest Approach ──────────────────────────────────────────────────────────

def test_closest_approach_returns_keys():
    result = closest_approach(**EARTH_ELEMENTS, days=10.0, steps=200)
    assert 't' in result
    assert 'km' in result
    assert 'ld' in result


def test_closest_approach_positive_distance():
    result = closest_approach(**APOPHIS_ELEMENTS, days=30.0, steps=300)
    assert result['km'] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
