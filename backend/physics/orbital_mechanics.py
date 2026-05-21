"""
Custom orbital mechanics physics engine.

Implements:
  - Keplerian orbital element computation from state vectors
  - Runge-Kutta 4 orbit propagator (Sun gravity only, two-body)
  - Monte Carlo uncertainty corridor (N=1000 runs)
  - Closest approach solver
"""

import math
import random
from typing import List, Tuple, Dict, Any

# ── Physical Constants ────────────────────────────────────────────────────────
MU_SUN = 1.32712440018e20      # m³/s²  — gravitational parameter of the Sun
AU = 1.495978707e11            # m      — astronomical unit
LD = 3.84402e8                 # m      — lunar distance
DAY = 86400.0                  # s/day


# ── State Vector → Keplerian Elements ────────────────────────────────────────

def state_to_keplerian(
    r: List[float],   # position [m] (x, y, z)
    v: List[float],   # velocity [m/s] (vx, vy, vz)
    mu: float = MU_SUN,
) -> Dict[str, float]:
    """
    Convert Cartesian state vector to Keplerian orbital elements.

    Returns dict with keys:
        a  – semi-major axis (AU)
        e  – eccentricity
        i  – inclination (deg)
        raan – right ascension of ascending node (deg) Ω
        argp – argument of perihelion (deg) ω
        M    – mean anomaly (deg)
        T    – orbital period (days)
    """
    rx, ry, rz = r
    vx, vy, vz = v

    r_mag = math.sqrt(rx**2 + ry**2 + rz**2)
    v_mag = math.sqrt(vx**2 + vy**2 + vz**2)

    # Angular momentum vector h = r × v
    hx = ry * vz - rz * vy
    hy = rz * vx - rx * vz
    hz = rx * vy - ry * vx
    h_mag = math.sqrt(hx**2 + hy**2 + hz**2)

    # Node vector n = ẑ × h
    nx = -hy
    ny = hx
    n_mag = math.sqrt(nx**2 + ny**2)

    # Eccentricity vector e_vec = (v×h)/μ - r̂
    e_coeff = v_mag**2 - mu / r_mag
    ex = (e_coeff * rx - (rx * vx + ry * vy + rz * vz) * vx) / mu
    ey = (e_coeff * ry - (rx * vx + ry * vy + rz * vz) * vy) / mu
    ez = (e_coeff * rz - (rx * vx + ry * vy + rz * vz) * vz) / mu
    e = math.sqrt(ex**2 + ey**2 + ez**2)

    # Specific orbital energy ε
    eps = v_mag**2 / 2.0 - mu / r_mag

    # Semi-major axis
    if abs(e - 1.0) < 1e-9:  # parabolic — degenerate
        a = float("inf")
    else:
        a = -mu / (2.0 * eps)

    # Inclination
    i = math.acos(max(-1.0, min(1.0, hz / h_mag)))

    # RAAN Ω
    if n_mag < 1e-9:
        raan = 0.0
    else:
        raan = math.acos(max(-1.0, min(1.0, nx / n_mag)))
        if ny < 0:
            raan = 2 * math.pi - raan

    # Argument of perihelion ω
    if n_mag < 1e-9 or e < 1e-9:
        argp = 0.0
    else:
        argp = math.acos(max(-1.0, min(1.0, (nx * ex + ny * ey) / (n_mag * e))))
        if ez < 0:
            argp = 2 * math.pi - argp

    # True anomaly ν
    rdotv = rx * vx + ry * vy + rz * vz
    if e < 1e-9:
        nu = 0.0
    else:
        nu = math.acos(max(-1.0, min(1.0, (ex * rx + ey * ry + ez * rz) / (e * r_mag))))
        if rdotv < 0:
            nu = 2 * math.pi - nu

    # Eccentric anomaly E (for elliptical)
    if e < 1.0:
        E = 2.0 * math.atan2(
            math.sqrt(1.0 - e) * math.sin(nu / 2.0),
            math.sqrt(1.0 + e) * math.cos(nu / 2.0),
        )
        M = E - e * math.sin(E)
    else:
        M = 0.0

    # Period
    T = 2 * math.pi * math.sqrt(a**3 / mu) / DAY if a > 0 and e < 1.0 else float("inf")

    return {
        "a": a / AU,
        "e": e,
        "i": math.degrees(i),
        "raan": math.degrees(raan),
        "argp": math.degrees(argp),
        "M": math.degrees(M) % 360.0,
        "T": T,
    }


# ── Keplerian Elements → State Vector ────────────────────────────────────────

def keplerian_to_state(
    a: float,    # AU
    e: float,
    i: float,    # deg
    raan: float, # deg
    argp: float, # deg
    M: float,    # deg (mean anomaly at epoch)
    mu: float = MU_SUN,
) -> Tuple[List[float], List[float]]:
    """
    Convert Keplerian elements to Cartesian state vector.
    Returns (r [m], v [m/s]).
    """
    a_m = a * AU
    i_r = math.radians(i)
    raan_r = math.radians(raan)
    argp_r = math.radians(argp)
    M_r = math.radians(M)

    # Solve Kepler's equation M = E - e*sin(E) via Newton-Raphson
    E = _solve_kepler(M_r, e)

    # True anomaly ν
    nu = 2.0 * math.atan2(
        math.sqrt(1.0 + e) * math.sin(E / 2.0),
        math.sqrt(1.0 - e) * math.cos(E / 2.0),
    )

    # Distance
    r_c = a_m * (1.0 - e * math.cos(E))

    # Perifocal coords
    x_p = r_c * math.cos(nu)
    y_p = r_c * math.sin(nu)

    vx_p = math.sqrt(mu * a_m) / r_c * (-math.sin(E))
    vy_p = math.sqrt(mu * a_m) / r_c * (math.sqrt(1.0 - e**2) * math.cos(E))

    # Rotation matrix (perifocal → ECI)
    r_eci = _peri_to_eci(x_p, y_p, 0.0, raan_r, i_r, argp_r)
    v_eci = _peri_to_eci(vx_p, vy_p, 0.0, raan_r, i_r, argp_r)

    return list(r_eci), list(v_eci)


def _solve_kepler(M: float, e: float, tol: float = 1e-10, max_iter: int = 50) -> float:
    """Newton-Raphson solver for Kepler's equation."""
    E = M if e < 0.8 else math.pi
    for _ in range(max_iter):
        dE = (E - e * math.sin(E) - M) / (1.0 - e * math.cos(E))
        E -= dE
        if abs(dE) < tol:
            break
    return E


def _peri_to_eci(x, y, z, raan, inc, argp):
    """Rotate perifocal vector to ECI."""
    cos_raan = math.cos(raan)
    sin_raan = math.sin(raan)
    cos_inc = math.cos(inc)
    sin_inc = math.sin(inc)
    cos_argp = math.cos(argp)
    sin_argp = math.sin(argp)

    # 3×3 rotation matrix rows
    Rx = cos_raan * cos_argp - sin_raan * sin_argp * cos_inc
    Ry = -cos_raan * sin_argp - sin_raan * cos_argp * cos_inc
    Rz = sin_raan * sin_inc

    Sx = sin_raan * cos_argp + cos_raan * sin_argp * cos_inc
    Sy = -sin_raan * sin_argp + cos_raan * cos_argp * cos_inc
    Sz = -cos_raan * sin_inc

    Wx = sin_argp * sin_inc
    Wy = cos_argp * sin_inc
    Wz = cos_inc

    return (
        Rx * x + Ry * y + Rz * z,
        Sx * x + Sy * y + Sz * z,
        Wx * x + Wy * y + Wz * z,
    )


# ── RK4 Two-Body Propagator ───────────────────────────────────────────────────

def _gravity(state: List[float], mu: float) -> List[float]:
    """Two-body gravitational acceleration [ax, ay, az] in m/s²."""
    x, y, z = state[0], state[1], state[2]
    r3 = (x**2 + y**2 + z**2) ** 1.5
    return [
        state[3], state[4], state[5],
        -mu * x / r3,
        -mu * y / r3,
        -mu * z / r3,
    ]


def _rk4_step(state: List[float], dt: float, mu: float) -> List[float]:
    """Single RK4 integration step."""
    k1 = _gravity(state, mu)
    s2 = [state[i] + 0.5 * dt * k1[i] for i in range(6)]
    k2 = _gravity(s2, mu)
    s3 = [state[i] + 0.5 * dt * k2[i] for i in range(6)]
    k3 = _gravity(s3, mu)
    s4 = [state[i] + dt * k3[i] for i in range(6)]
    k4 = _gravity(s4, mu)
    return [state[i] + dt * (k1[i] + 2*k2[i] + 2*k3[i] + k4[i]) / 6.0 for i in range(6)]


def propagate_orbit(
    a: float, e: float, i: float, raan: float, argp: float, M: float,
    days: float = 30.0,
    steps: int = 300,
    mu: float = MU_SUN,
) -> List[Dict[str, float]]:
    """
    Propagate orbit from initial Keplerian elements over `days` days.

    Returns list of {t, x, y, z} in AU for easy Three.js consumption.
    """
    r0, v0 = keplerian_to_state(a, e, i, raan, argp, M, mu)
    state = r0 + v0
    dt = days * DAY / steps
    path = []
    for step in range(steps + 1):
        t = step * days / steps
        x, y, z = state[0], state[1], state[2]
        path.append({"t": t, "x": x / AU, "y": y / AU, "z": z / AU})
        state = _rk4_step(state, dt, mu)
    return path


# ── Monte Carlo Uncertainty Corridor ─────────────────────────────────────────

def monte_carlo_approach(
    a: float, e: float, i: float, raan: float, argp: float, M: float,
    sigma_r_km: float = 100.0,   # 1-σ positional uncertainty in km
    sigma_v_ms: float = 10.0,    # 1-σ velocity uncertainty in m/s
    n_runs: int = 1000,
    target_r_m: Tuple[float, float, float] = (AU, 0.0, 0.0),  # Earth at 1 AU
    days: float = 30.0,
    mu: float = MU_SUN,
) -> Dict[str, Any]:
    """
    Monte Carlo simulation (N runs) over positional and velocity uncertainty.

    Returns:
        {
          "mean_miss_km": float,
          "std_miss_km": float,
          "p05_miss_km": float,   # 5th percentile
          "p95_miss_km": float,   # 95th percentile
          "mean_miss_ld": float,
          "corridor": List[{t, x_lo, x_hi, y_lo, y_hi, z_lo, z_hi}]  # AU
        }
    """
    sigma_r_m = sigma_r_km * 1000.0
    r0_base, v0_base = keplerian_to_state(a, e, i, raan, argp, M, mu)

    steps = 300
    dt = days * DAY / steps
    all_paths: List[List[List[float]]] = []
    min_distances_km: List[float] = []

    for _ in range(n_runs):
        # Perturb initial conditions
        r0 = [r0_base[j] + random.gauss(0, sigma_r_m) for j in range(3)]
        v0 = [v0_base[j] + random.gauss(0, sigma_v_ms) for j in range(3)]
        state = r0 + v0

        positions: List[List[float]] = []
        min_d = float("inf")
        for _ in range(steps + 1):
            pos = state[:3]
            d = math.sqrt(
                (pos[0] - target_r_m[0])**2
                + (pos[1] - target_r_m[1])**2
                + (pos[2] - target_r_m[2])**2
            )
            if d < min_d:
                min_d = d
            positions.append(pos)
            state = _rk4_step(state, dt, mu)

        min_distances_km.append(min_d / 1000.0)
        all_paths.append(positions)

    min_distances_km.sort()
    mean_miss = sum(min_distances_km) / n_runs
    variance = sum((d - mean_miss)**2 for d in min_distances_km) / n_runs
    std_miss = math.sqrt(variance)
    p05 = min_distances_km[int(0.05 * n_runs)]
    p95 = min_distances_km[int(0.95 * n_runs)]

    # Build spatial corridor (per-step envelope across runs)
    corridor = []
    for step in range(steps + 1):
        xs = [all_paths[run][step][0] / AU for run in range(n_runs)]
        ys = [all_paths[run][step][1] / AU for run in range(n_runs)]
        zs = [all_paths[run][step][2] / AU for run in range(n_runs)]
        corridor.append({
            "t": step * days / steps,
            "x_lo": min(xs), "x_hi": max(xs),
            "y_lo": min(ys), "y_hi": max(ys),
            "z_lo": min(zs), "z_hi": max(zs),
        })

    return {
        "mean_miss_km": mean_miss,
        "std_miss_km": std_miss,
        "p05_miss_km": p05,
        "p95_miss_km": p95,
        "mean_miss_ld": mean_miss * 1000.0 / (LD / 1000.0),
        "corridor": corridor,
        "histogram_km": min_distances_km[::10],  # thin to 100 points for transfer
    }


# ── Closest Approach Finder ───────────────────────────────────────────────────

def closest_approach(
    a: float, e: float, i: float, raan: float, argp: float, M: float,
    days: float = 30.0,
    steps: int = 3000,
    target_r_m: Tuple[float, float, float] = (AU, 0.0, 0.0),
    mu: float = MU_SUN,
) -> Dict[str, float]:
    """Return t (days), distance in km and LD of closest approach."""
    r0, v0 = keplerian_to_state(a, e, i, raan, argp, M, mu)
    state = r0 + v0
    dt = days * DAY / steps
    best = {"t": 0.0, "km": float("inf"), "ld": float("inf")}
    for step in range(steps + 1):
        x, y, z = state[0], state[1], state[2]
        d = math.sqrt(
            (x - target_r_m[0])**2 + (y - target_r_m[1])**2 + (z - target_r_m[2])**2
        )
        d_km = d / 1000.0
        if d_km < best["km"]:
            best = {"t": step * days / steps, "km": d_km, "ld": d / LD}
        state = _rk4_step(state, dt, mu)
    return best
