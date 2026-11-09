"""P3: exposure dose of points and lines with the Gaussian kernel (spezifikation §3.4–§3.6)."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from voxelspaetzle.dose import Grid, VolumeField, dose_field
from voxelspaetzle.focus import GaussFocus
from voxelspaetzle.path import KIND_HATCH, KIND_POINT, Job, Layer, Segments, WritePath

W0, WZ = 0.4, 1.2
FOCUS = GaussFocus(w0_um=W0, wz_um=WZ)


def single(start, end, power, speed, kind=KIND_HATCH, dwell=0.0) -> WritePath:  # type: ignore[no-untyped-def]
    one = np.ones(1)
    seg = Segments(
        np.array([start], dtype=float),
        np.array([end], dtype=float),
        power * one,
        speed * one,
        np.full(1, kind, dtype=np.int8),
        dwell * one,
        np.zeros(1, dtype=np.int32),
        np.zeros(1, dtype=np.int32),
    )
    return WritePath("test", [Job("IP-S", [Layer(float(start[2]), 0.0, seg)])])


def centres(grid: Grid) -> tuple[np.ndarray, np.ndarray, np.ndarray]:  # type: ignore[type-arg]
    z, y, x = (
        grid.origin_um[k] + (np.arange(grid.shape[2 - k]) + 0.5) * grid.step_um[k]
        for k in (2, 1, 0)
    )
    return z[:, None, None], y[None, :, None], x[None, None, :]


def test_kernel_is_normalized_in_the_focal_plane() -> None:
    h = 0.01
    x = np.arange(-4, 4, h) + h / 2
    g = FOCUS.g(x[None, :], x[:, None], np.zeros(1)[:, None])
    assert g.sum() * h * h == pytest.approx(1.0, rel=1e-9)


def test_point_on_a_node_is_exact() -> None:
    grid = Grid(origin_um=(-2.05, -2.05, -4.05), step_um=(0.1, 0.1, 0.1), shape=(81, 41, 41))
    path = single(
        (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), power=10.0, speed=1.0, kind=KIND_POINT, dwell=0.5
    )
    d = dose_field(path, grid, FOCUS).data["dose_mW2s_per_um4"]
    z, y, x = centres(grid)
    d0 = 10.0**2 * (2 / (math.pi * W0**2)) ** 2 * 0.5
    expected = d0 * np.exp(-4 * (x**2 + y**2) / W0**2 - 4 * z**2 / WZ**2)
    np.testing.assert_allclose(d, expected, rtol=0, atol=1e-12 * d0)


def test_line_profile_matches_the_analytic_gauss() -> None:
    grid = Grid(origin_um=(-6.05, -1.55, -3.55), step_um=(0.1, 0.1, 0.1), shape=(71, 31, 121))
    path = single((-5.0, 0.0, 0.0), (5.0, 0.0, 0.0), power=20.0, speed=1e3)
    d = dose_field(path, grid, FOCUS).data["dose_mW2s_per_um4"]
    z, y, _ = centres(grid)
    d0 = 20.0**2 * (2 / (math.pi * W0**2)) ** 2 * (math.sqrt(math.pi) * W0 / 2) / 1e3
    expected = d0 * np.exp(-4 * y**2 / W0**2 - 4 * z**2 / WZ**2)
    mid = slice(30, 91)  # |x| ≤ 3 µm, far from the line ends
    np.testing.assert_allclose(
        d[:, :, mid], np.broadcast_to(expected, d[:, :, mid].shape), rtol=0, atol=1e-6 * d0
    )


def test_off_node_line_converges() -> None:
    errors = []
    for h in (0.1, 0.05, 0.025):
        ny = int(round(2.0 / h))
        grid = Grid(origin_um=(-0.55, -1.0, -2.05), step_um=(0.1, h, 0.1), shape=(41, ny, 11))
        y0 = 0.3 * h  # line between the nodes in y
        path = single((-6.0, y0, 0.0), (6.0, y0, 0.0), power=20.0, speed=1e3)
        d = dose_field(path, grid, FOCUS).data["dose_mW2s_per_um4"]
        z, y, _ = centres(grid)
        d0 = 20.0**2 * (2 / (math.pi * W0**2)) ** 2 * (math.sqrt(math.pi) * W0 / 2) / 1e3
        expected = d0 * np.exp(-4 * (y - y0) ** 2 / W0**2 - 4 * z**2 / WZ**2)
        errors.append(float(np.abs(d - expected).max() / d0))
    assert errors[0] < 0.05
    assert errors[2] < errors[1] / 3 < errors[0] / 9  # second order in the grid step


def test_power_speed_scaling_and_linear_accumulation() -> None:
    grid = Grid(origin_um=(-3.0, -1.5, -3.0), step_um=(0.1, 0.1, 0.1), shape=(60, 30, 60))
    a = dose_field(single((-2, 0, 0), (2, 0, 0), 10.0, 1e3), grid, FOCUS).data["dose_mW2s_per_um4"]
    b = dose_field(single((-2, 0, 0), (2, 0, 0), 20.0, 2e3), grid, FOCUS).data["dose_mW2s_per_um4"]
    np.testing.assert_allclose(b, 2.0 * a, rtol=1e-12, atol=1e-15 * a.max())
    left = single((-2, 0, 0), (0, 0, 0), 10.0, 1e3)
    right = single((0, 0, 0), (2, 0, 0), 10.0, 1e3)
    both = WritePath("test", left.jobs + right.jobs)
    c = dose_field(both, grid, FOCUS).data["dose_mW2s_per_um4"]
    np.testing.assert_allclose(c, a, rtol=0, atol=1e-9 * a.max())


def test_attenuation_scales_quadratically() -> None:
    grid = Grid(origin_um=(-1.0, -1.0, -2.0), step_um=(0.1, 0.1, 0.1), shape=(40, 20, 20))
    p = single((0, 0, 0), (0, 0, 0), 10.0, 1.0, kind=KIND_POINT, dwell=1.0)
    full = dose_field(p, grid, FOCUS).data["dose_mW2s_per_um4"]
    weak = dose_field(p, grid, FOCUS, power_factor=0.7).data["dose_mW2s_per_um4"]
    np.testing.assert_allclose(weak, 0.49 * full, rtol=1e-12, atol=1e-12 * full.max())


def test_field_file_roundtrip(tmp_path: Path) -> None:
    grid = Grid(origin_um=(-1.0, -1.0, -2.0), step_um=(0.1, 0.1, 0.1), shape=(40, 20, 20))
    f = dose_field(single((0, 0, 0), (0, 0, 0), 10.0, 1.0, kind=KIND_POINT, dwell=1.0), grid, FOCUS)
    f.save(tmp_path / "dose.json")
    g = VolumeField.load(tmp_path / "dose.json")
    assert g.grid == f.grid and g.focus == {"kind": "gauss", "w0_um": W0, "wz_um": WZ}
    assert g.data["dose_mW2s_per_um4"].tobytes() == f.data["dose_mW2s_per_um4"].tobytes()


def test_invalid_input() -> None:
    with pytest.raises(ValueError):
        GaussFocus(w0_um=0.0, wz_um=1.0)
    with pytest.raises(ValueError):
        Grid(origin_um=(0, 0, 0), step_um=(0.1, 0.0, 0.1), shape=(2, 2, 2))
