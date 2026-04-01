# fluid_solver.py
# A lightweight "fluid two-threshold" solver for GI/GI/N+GI under overload.
#
# It proposes (w_l, w_h, p) where service is concentrated at two waiting times
# and the mixture p is chosen to satisfy the capacity (served-fraction) balance.
#
# Supports two objectives:
#   - objective="queue_length": r(w)=hazard=h(w)=f(w)/S(w), cost c(w)=∫_0^w S(y) dy
#   - objective="offered_wait": r(w)=density=f(w), cost c(w)=w
#

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Optional, Literal
import numpy as np

Objective = Literal["queue_length", "offered_wait"]


@dataclass(frozen=True)
class FluidSolution:
    w_l: float
    w_h: float
    p: float
    level: float
    obj_value: float


def _bisect_root(
    f: Callable[[float], float],
    a: float,
    b: float,
    fa: float,
    fb: float,
    tol: float = 1e-8,
    max_iter: int = 200,
) -> float:
    # Assumes fa and fb have opposite signs or one is zero.
    if fa == 0.0:
        return a
    if fb == 0.0:
        return b
    lo = a
    hi = b
    flo = fa
    fhi = fb
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        fmid = f(mid)
        if abs(fmid) <= tol or (hi - lo) <= tol:
            return mid
        if flo * fmid <= 0.0:
            hi = mid
            fhi = fmid
        else:
            lo = mid
            flo = fmid
    return 0.5 * (lo + hi)


def _find_level_set_roots(
    r: Callable[[float], float],
    level: float,
    w_grid: np.ndarray,
    tol: float = 1e-8,
) -> list[float]:
    # Find roots of r(w) - level using sign changes on the grid + bisection.
    g = lambda w: r(w) - level
    vals = np.array([g(w) for w in w_grid], dtype=float)

    roots: list[float] = []
    for i in range(len(w_grid) - 1):
        a = float(w_grid[i])
        b = float(w_grid[i + 1])
        fa = float(vals[i])
        fb = float(vals[i + 1])

        if fa == 0.0:
            roots.append(a)
            continue
        if fa * fb < 0.0 or fb == 0.0:
            root = _bisect_root(g, a, b, fa, fb, tol=tol)
            roots.append(root)

    # Deduplicate near-equal roots
    roots.sort()
    dedup: list[float] = []
    for x in roots:
        if not dedup or abs(x - dedup[-1]) > 1e-5:
            dedup.append(x)
    return dedup


def _cost_offered_wait(w: float) -> float:
    return w


def _cost_queue_length(w: float, S: Callable[[float], float], n_int: int = 400) -> float:
    # c(w)=∫_0^w S(y) dy using trapezoid rule
    if w <= 0.0:
        return 0.0
    ys = np.linspace(1e-10, w, n_int)
    vals = np.array([S(float(y)) for y in ys], dtype=float)
    return float(np.trapz(vals, ys))


def solve_two_threshold_fluid(
    *,
    objective: Objective,
    # patience distribution primitives
    patience: Callable[[float], float],  # density f(w)
    # overload parameters
    lam: float,                     # arrival rate λ
    n_servers: int,                 # N
    mean_service: float,            # E[S_service] = m
    # numerical controls
    w_max: float = 50.0,
    n_grid: int = 4000,
    n_levels: int = 250,
    level_quantiles: tuple[float, float] = (0.05, 0.995),
    tol: float = 1e-8,
) -> Optional[FluidSolution]:
    """
    Returns the best (w_l, w_h, p) found, or None if no feasible pair is found.

    Core conditions used:
      1) Equal-index: r(w_l)=r(w_h)=level
      2) Capacity balance via served fraction:
           served_fraction = (N / mean_service) / λ
         Two-point mixture requires:
           p*S(w_l) + (1-p)*S(w_h) = served_fraction

    Then it picks the feasible pair minimizing:
      - offered_wait: p*w_l + (1-p)*w_h
      - queue_length: p*∫_0^{w_l} S + (1-p)*∫_0^{w_h} S
    """
    if lam <= 0.0:
        raise ValueError("lam must be > 0")
    if n_servers <= 0:
        raise ValueError("n_servers must be > 0")
    if mean_service <= 0.0:
        raise ValueError("mean_service must be > 0")
    if w_max <= 0.0:
        raise ValueError("w_max must be > 0")

    capacity = n_servers / mean_service
    served_fraction = capacity / lam

    f = patience.pdf
    S = patience.survival

    # In overload we expect served_fraction < 1, but allow <=1.
    if served_fraction <= 0.0:
        return None
    if served_fraction >= 1.0:
        # Not overloaded. Two-point construction is not the relevant regime.
        # Return trivial "serve immediately" suggestion.
        return FluidSolution(w_l=0.0, w_h=0.0, p=1.0, level=float("nan"), obj_value=0.0)

    if objective == "queue_length":
        if hasattr(patience, "hazard"):
            r = patience.hazard
        else:
            def r(w: float) -> float:
                sw = S(w)
                if sw <= 0.0:
                    return float("inf")
                return f(w) / sw
        cost = lambda w: _cost_queue_length(w, S)
    elif objective == "offered_wait":
        r = f
        cost = _cost_offered_wait
    else:
        raise ValueError("objective must be 'queue_length' or 'offered_wait'")

    # Build w grid
    w_grid = np.linspace(1e-10, w_max, n_grid)

    # Build a grid of candidate "levels" for r(w).
    # We use quantiles of r(w_grid) to avoid crazy tails.
    r_vals = np.array([r(float(w)) for w in w_grid], dtype=float)
    r_vals = r_vals[np.isfinite(r_vals)]
    if len(r_vals) < 10:
        return None

    lo_q, hi_q = level_quantiles
    lo = float(np.quantile(r_vals, lo_q))
    hi = float(np.quantile(r_vals, hi_q))
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        return None

    levels = np.linspace(lo, hi, n_levels)

    best: Optional[FluidSolution] = None

    for level in levels:
        roots = _find_level_set_roots(r, float(level), w_grid, tol=tol)
        if len(roots) < 2:
            continue

        # Consider all pairs (w_l, w_h) with w_l < w_h
        for i in range(len(roots) - 1):
            for j in range(i + 1, len(roots)):
                w_l = float(roots[i])
                w_h = float(roots[j])

                Sl = float(S(w_l))
                Sh = float(S(w_h))

                denom = (Sl - Sh)
                if abs(denom) < 1e-12:
                    continue

                # Solve p from p*Sl + (1-p)*Sh = served_fraction
                p = (served_fraction - Sh) / denom

                if p < -1e-9 or p > 1.0 + 1e-9:
                    continue
                p = min(1.0, max(0.0, float(p)))

                obj_value = p * cost(w_l) + (1.0 - p) * cost(w_h)

                sol = FluidSolution(
                    w_l=w_l,
                    w_h=w_h,
                    p=p,
                    level=float(level),
                    obj_value=float(obj_value),
                )

                if best is None or sol.obj_value < best.obj_value:
                    best = sol

    return best
