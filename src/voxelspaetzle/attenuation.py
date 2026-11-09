"""Attenuation of the writing beam on its way to the focus (spezifikation §3.3, Testfall P12)."""

from __future__ import annotations

import math
from itertools import pairwise

import numpy as np


def kappa_from_alpha_per_mm(alpha_per_mm: float, wavelength_um: float) -> float:
    """κ = α λ / (4π) (D7; α intensity coefficient in 1/mm, base e)."""
    return alpha_per_mm * wavelength_um * 1e-3 / (4.0 * math.pi)


def alpha_per_mm_from_kappa(kappa: float, wavelength_um: float) -> float:
    """α = 4π κ / λ in 1/mm."""
    return 4.0 * math.pi * kappa / (wavelength_um * 1e-3)


def focus_power_mW(
    power_mW: float,
    kappa: float,
    wavelength_um: float,
    path_um: float | None,
    t_objective: float = 1.0,
) -> float:
    """P_f = P · T_obj · exp(−4πκL/λ) on the axis (§3.3); L = ``path_um`` (resist_path_um)."""
    if kappa == 0.0:
        return power_mW * t_objective
    if path_um is None:
        raise ValueError("absorbing resist: resist_path_um (L) is needed for the attenuation")
    a = 4.0 * math.pi * kappa * path_um / wavelength_um
    return power_mW * t_objective * math.exp(-a)


def cone_transmission(a: float, sin_max: float, nodes: int = 64) -> float:
    """Transmission exp(−a/cos θ) averaged over a uniformly filled pupil (§3.3).

    Weight sin θ cos θ dθ up to sin θ_m = NA/n; a = 4πκL/λ is the axial optical depth. Composite
    Gauss–Legendre over u = 1/cos θ ∈ [1, 1/cos θ_m] of e^(−a u) u⁻³ (smooth, 8 panels).
    """
    if not 0.0 < sin_max < 1.0:
        raise ValueError("sin_max = NA/n must lie in (0, 1)")
    um = 1.0 / math.sqrt(1.0 - sin_max * sin_max)
    x, w = np.polynomial.legendre.leggauss(nodes)
    total = 0.0
    for lo, hi in pairwise(np.linspace(1.0, um, 9).tolist()):
        u = 0.5 * (hi - lo) * x + 0.5 * (hi + lo)
        total += 0.5 * (hi - lo) * float(np.dot(w, np.exp(-a * u) / u**3))
    return 2.0 * total / (sin_max * sin_max)
