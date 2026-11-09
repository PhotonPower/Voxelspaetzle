"""P22, P21: printed gratings in FourierGrating (spezifikation §3.12).

Needs the ``fouriergrating`` package (built from source in CI). Locally the tests are skipped
without it; with ``VOXELSPAETZLE_REQUIRE_FG=1`` (set in CI) a missing package is an error.
"""

from __future__ import annotations

import math
import os
from typing import Any

import numpy as np
import pytest

from voxelspaetzle.dose import DOSE, Grid, VolumeField, dose_field
from voxelspaetzle.export import fourier_grating_layers
from voxelspaetzle.focus import GaussFocus
from voxelspaetzle.path import KIND_HATCH, Job, Layer, Segments, WritePath
from voxelspaetzle.polymerization import ThresholdModel, degree_of_polymerization

if os.environ.get("VOXELSPAETZLE_REQUIRE_FG") == "1":
    import fouriergrating as fg
else:
    fg = pytest.importorskip("fouriergrating")

PERIOD, LAM, N_RESIST = 10.0, 0.55, 1.52
HEIGHT = LAM / (N_RESIST - 1)  # phase step of one wavelength in transmission


def staircase(steps: int) -> VolumeField:
    """Ideal voxel blaze: ``steps`` columns, the i-th one i + 1 voxels high, over one period."""
    a = np.zeros((steps, 1, steps))
    for i in range(steps):
        a[: i + 1, 0, i] = 1.0
    grid = Grid((0.0, 0.0, 0.0), (PERIOD / steps, 1.0, HEIGHT / steps), (steps, 1, steps))
    return VolumeField(grid, {"alpha": a})


def solve(layers: list[dict[str, Any]], nx: int = 61) -> Any:
    cfg = {
        "dimension": "1D",
        "solver": "rcwa",
        "truncation": {"Nx": nx, "Nz": 0},
        "period_um": {"x": PERIOD, "z": 0.0},
        "incidence": {"lambda_um": LAM, "phi_deg": 0, "psi_deg": 0, "delta_deg": 0},
        "materials": {"air": {"n": 1.0}, "IP-Dip": {"n": N_RESIST}},
        "superstrate": "air",
        "substrate": "IP-Dip",
        "layers": layers,
    }
    return fg.solve(cfg)


def first_order(result: Any) -> float:
    t = result.transmitted
    return float(t["eff"][t["n"] == 1][0])


def test_orders_follow_the_grating_equation_and_energy_is_conserved() -> None:
    _, layers = fourier_grating_layers(staircase(4), 0, "IP-Dip", "air")
    r = solve(layers)
    # propagating orders: |m| λ/Λ ≤ n of the half-space
    assert set(r.transmitted["n"]) == set(range(-27, 28))  # 1.52 · 10 / 0.55 = 27.6
    assert set(r.reflected["n"]) == set(range(-18, 19))  # 10 / 0.55 = 18.2
    assert abs(1.0 - r.diagnostics["energy_balance"]) < 1e-5


def test_blaze_efficiency_grows_with_the_number_of_steps() -> None:
    """Scalar estimate for N steps: T_Fresnel · sinc²(1/N); rigorous lies a few % below."""
    fresnel = 1.0 - ((N_RESIST - 1) / (N_RESIST + 1)) ** 2
    eff = {}
    for steps in (4, 8):
        _, layers = fourier_grating_layers(staircase(steps), 0, "IP-Dip", "air")
        eff[steps] = first_order(solve(layers))
        x = 1.0 / steps
        scalar = fresnel * (math.sin(math.pi * x) / (math.pi * x)) ** 2
        assert eff[steps] == pytest.approx(scalar, abs=0.06)
    assert eff[8] > eff[4]


def test_printed_profile_loses_efficiency_against_the_design() -> None:
    """P21 (qualitative): the printed blaze is only approximated; first order drops."""
    steps = 8
    hx, hz = PERIOD / steps, HEIGHT / steps
    pts = [
        (p * PERIOD + (i + 0.5) * hx, (k + 0.5) * hz)
        for p in (-1, 0, 1)
        for i in range(steps)
        for k in range(i + 1)
    ]
    m = len(pts)
    xs, zs = np.array([q[0] for q in pts]), np.array([q[1] for q in pts])
    seg = Segments(
        np.column_stack([xs, np.full(m, -20.0), zs]),
        np.column_stack([xs, np.full(m, 20.0), zs]),
        np.full(m, 10.0),
        np.full(m, 1e4),
        np.full(m, KIND_HATCH, dtype=np.int8),
        np.zeros(m),
        np.zeros(m, dtype=np.int32),
        np.zeros(m, dtype=np.int32),
    )
    path = WritePath("test", [Job("IP-Dip", [Layer(0.0, 0.0, seg)])])
    grid = Grid((0.0, -0.05, 0.0), (PERIOD / 100, 0.1, 0.05), (26, 1, 100))
    f = dose_field(path, grid, GaussFocus(0.3, 0.9))
    plateau = float(np.median(f.data[DOSE][1:4, 0, 75:95]))
    alpha = degree_of_polymerization(f, ThresholdModel(0.5 * plateau))
    _, layers = fourier_grating_layers(alpha, 0, "IP-Dip", "air")
    _, ideal = fourier_grating_layers(staircase(steps), 0, "IP-Dip", "air")
    printed, design = first_order(solve(layers)), first_order(solve(ideal))
    assert 0.0 < printed < design
