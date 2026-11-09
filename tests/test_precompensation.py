"""V8b: proximity correction and pre-compensation (spezifikation §3.14, Testfälle P29, P30)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from voxelspaetzle.dose import DOSE, Grid, dose_field
from voxelspaetzle.focus import GaussFocus
from voxelspaetzle.path import KIND_HATCH, Job, Layer, Segments, WritePath
from voxelspaetzle.precompensation import (
    proximity_correction,
    scale_path,
    segment_kernel,
    solve_parameter,
)
from voxelspaetzle.threshold import line_size

FOCUS = GaussFocus(0.4, 1.2)
G2 = (2 / (math.pi * 0.4**2)) ** 2
END_TOL = 2e-2  # fraction of the peak dose, see the test


def lines(ys: list[float], power: float = 20.0, z: float = 0.0, half: float = 3.0) -> WritePath:
    n = len(ys)
    one = np.ones(n)
    seg = Segments(
        np.column_stack([np.full(n, -half), ys, np.full(n, z)]),
        np.column_stack([np.full(n, half), ys, np.full(n, z)]),
        power * one,
        1e3 * one,
        np.full(n, KIND_HATCH, dtype=np.int8),
        0.0 * one,
        np.zeros(n, dtype=np.int32),
        np.zeros(n, dtype=np.int32),
    )
    return WritePath("test", [Job("IP-S", [Layer(z, 0.0, seg)])])


def test_segment_kernel_matches_the_dose_engine() -> None:
    """Closed form (erf) of the line integral against the gridded dose (P29)."""
    path = lines([-0.3, 0.0, 0.2])  # on grid nodes in y
    grid = Grid((-3.95, -0.95, -0.95), (0.1, 0.1, 0.1), (19, 19, 79))
    d = dose_field(path, grid, FOCUS).data[DOSE]
    xs = np.array([-2.0, 0.0, 2.9, 3.4])  # cell centres; the last two near the line end x = 3
    pts = np.column_stack([xs, np.full(4, 0.1), np.zeros(4)])
    k = segment_kernel(pts, path, FOCUS)  # (points, segments), dose per P² (mW²)
    pred = k @ (path.jobs[0].layers[0].segments.power_mW ** 2)
    ix = np.round((xs + 3.95) / 0.1 - 0.5).astype(int)
    got = d[9, 10, ix]  # z = 0, y = 0.1
    np.testing.assert_allclose(pred[:2], got[:2], rtol=1e-9)  # interior: exact
    # at the line end the grid spreads the deposit trilinearly over h = 0.1 µm along x:
    # error ≤ h²/12·|D''| ≈ 4 % of the peak (σ = w₀/(2√2)); measured 1.2 %
    np.testing.assert_allclose(pred[2:], got[2:], rtol=0, atol=END_TOL * got.max())


def test_isolated_line_gets_the_analytic_power() -> None:
    target = 2.0e3
    out = proximity_correction(lines([0.0], half=50.0), FOCUS, target)
    p = out.jobs[0].layers[0].segments.power_mW[0]
    expected = math.sqrt(target / (G2 * math.sqrt(math.pi) * 0.4 / 2 / 1e3))
    assert p == pytest.approx(expected, rel=1e-9)


def test_hatched_field_reaches_the_target_dose_everywhere() -> None:
    ys = [k * 0.25 for k in range(-8, 9)]
    path = lines(ys)
    target = 5.0e3
    out = proximity_correction(path, FOCUS, target)
    seg = out.jobs[0].layers[0].segments
    mids = 0.5 * (seg.start_um + seg.end_um)
    dose = segment_kernel(mids, out, FOCUS) @ seg.power_mW**2
    np.testing.assert_allclose(dose, target, rtol=1e-9)
    p = seg.power_mW
    assert p[0] > p[8] and p[-1] > p[8]  # edge lines get less neighbour dose
    np.testing.assert_allclose(p, p[::-1], rtol=1e-9)  # symmetric
    assert out.source["proximity_correction"]["target_dose_mW2s_per_um4"] == target
    assert path.jobs[0].layers[0].segments.power_mW[0] == 20.0  # input unchanged


def test_scale_path_about_a_point() -> None:
    path = lines([0.0, 1.0], z=2.0)
    out = scale_path(path, (1.0, 1.0, 1.28), centre_um=(0.0, 0.0, 0.0))
    s0, s1 = path.jobs[0].layers[0], out.jobs[0].layers[0]
    np.testing.assert_allclose(s1.segments.start_um[:, 2], 1.28 * s0.segments.start_um[:, 2])
    np.testing.assert_allclose(s1.segments.start_um[:, :2], s0.segments.start_um[:, :2])
    assert s1.z_um == pytest.approx(2.56)
    with pytest.raises(ValueError):
        scale_path(path, (0.0, 1.0, 1.0))


def test_power_for_a_target_line_width_through_the_chain() -> None:
    """Inverse of P4: the power that prints a 0.5 µm line, against the closed form (P30)."""
    grid = Grid((-0.55, -1.01, -2.025), (0.1, 0.02, 0.05), (81, 101, 11))
    d_th = 0.3 * 20.0**2 * G2 * (math.sqrt(math.pi) * 0.4 / 2) / 1e3
    target = 0.5

    def width(power: float) -> float:
        path = lines([0.0], power=power, half=8.0)
        return line_size(dose_field(path, grid, FOCUS), d_th, x_um=0.0).width_um

    sol = solve_parameter(width, target, 15.0, 30.0, tol=1e-6)
    expected = math.sqrt(
        d_th * math.exp((target / 0.4) ** 2) / (G2 * math.sqrt(math.pi) * 0.4 / 2 / 1e3)
    )
    assert sol.converged and abs(sol.value - target) < 1e-6
    # width interpolation ≈ 1.5·10⁻³ maps to the power as ln(D₀/D_th)·1.5·10⁻³ ≈ 2.4·10⁻³
    assert sol.x == pytest.approx(expected, rel=4e-3)
    assert len(sol.history) <= 12
