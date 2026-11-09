"""P4, P5: threshold model, line widths, height maps and roughness (spezifikation §3.6)."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray

from voxelspaetzle.dose import Grid, dose_field
from voxelspaetzle.focus import GaussFocus
from voxelspaetzle.path import KIND_HATCH, Job, Layer, Segments, WritePath
from voxelspaetzle.threshold import (
    HeightMap,
    gauss_line_size,
    height_map,
    line_size,
    solid_field,
    spectrum,
    wall_profile,
)

W0, WZ = 0.4, 1.2
FOCUS = GaussFocus(W0, WZ)
G2 = (2 / (math.pi * W0**2)) ** 2


def lines(ys: list[float], zs: list[float], power: float = 20.0, speed: float = 1e3) -> WritePath:
    """Lines along x from −8 to 8 µm at all (y, z) combinations."""
    layers = []
    for z in zs:
        n = len(ys)
        one = np.ones(n)
        seg = Segments(
            np.column_stack([np.full(n, -8.0), ys, np.full(n, z)]),
            np.column_stack([np.full(n, 8.0), ys, np.full(n, z)]),
            power * one,
            speed * one,
            np.full(n, KIND_HATCH, dtype=np.int8),
            0.0 * one,
            np.zeros(n, dtype=np.int32),
            np.zeros(n, dtype=np.int32),
        )
        layers.append(Layer(z, 0.0, seg))
    return WritePath("test", [Job("IP-S", layers)])


def line_d0(power: float, speed: float) -> float:
    return power**2 * G2 * (math.sqrt(math.pi) * W0 / 2) / speed


GRID = Grid(origin_um=(-0.55, -1.01, -2.025), step_um=(0.1, 0.02, 0.05), shape=(81, 101, 11))


@pytest.mark.parametrize(("power", "speed"), [(20.0, 1e3), (15.0, 1e3), (20.0, 2e3)])
def test_line_width_and_height_follow_the_gauss_law(power: float, speed: float) -> None:
    f = dose_field(lines([0.0], [0.0], power, speed), GRID, FOCUS)
    d_th = 0.3 * line_d0(20.0, 1e3)
    size = line_size(f, d_th, x_um=0.0)
    exp_w, exp_h = gauss_line_size(FOCUS, line_d0(power, speed), d_th)
    assert size.width_um == pytest.approx(exp_w, rel=2e-3)
    assert size.height_um == pytest.approx(exp_h, rel=2e-3)
    assert size.fwhm_um == pytest.approx(W0 * math.sqrt(math.log(2)), rel=2e-3)


def test_below_threshold_nothing_is_printed() -> None:
    f = dose_field(lines([0.0], [0.0]), GRID, FOCUS)
    size = line_size(f, 1.01 * line_d0(20.0, 1e3), x_um=0.0)
    assert size.width_um == 0.0 and size.height_um == 0.0
    assert not solid_field(f, 1.01 * line_d0(20.0, 1e3), "IP-S").data["material"].any()


def test_warning_below_40_percent_of_the_dose_fwhm() -> None:
    f = dose_field(lines([0.0], [0.0]), GRID, FOCUS)
    d0 = line_d0(20.0, 1e3)
    assert not line_size(f, 0.5 * d0, x_um=0.0).unreliable
    assert line_size(f, d0 / 1.08, x_um=0.0).unreliable  # width/FWHM = √(ln 1.08 / ln 2) ≈ 0.33


def test_width_sensitivity_to_power() -> None:
    """Δd/d ≈ (ΔP/P)/ln(D₀/D_th) (§3.6; fischer2013, Abschn. 4.3)."""
    d_th = 0.3 * line_d0(20.0, 1e3)
    a = line_size(dose_field(lines([0.0], [0.0], 20.0), GRID, FOCUS), d_th, x_um=0.0)
    b = line_size(dose_field(lines([0.0], [0.0], 20.2), GRID, FOCUS), d_th, x_um=0.0)
    measured = (b.width_um - a.width_um) / a.width_um / 0.01
    assert measured == pytest.approx(1 / math.log(1 / 0.3), rel=2e-2)
    assert a.width_sensitivity == pytest.approx(1 / math.log(1 / 0.3), rel=1e-12)


def test_hatching_ripple_of_the_top_surface() -> None:
    h = 0.3
    ys = [k * h for k in range(-12, 13)]
    grid = Grid(origin_um=(-0.55, -1.5, -0.005), step_um=(0.1, 0.01, 0.01), shape=(101, 300, 11))
    f = dose_field(lines(ys, [0.0]), grid, FOCUS)
    d0 = line_d0(20.0, 1e3)
    d_th = 0.6 * d0  # mean line sum ≈ 1.18 D₀, top surface near z ≈ 0.49 µm
    hm = height_map(f, d_th)
    y = grid.origin_um[1] + (np.arange(grid.shape[1]) + 0.5) * grid.step_um[1]
    s = d0 * np.exp(-4 * (y[:, None] - np.array(ys)[None, :]) ** 2 / W0**2).sum(axis=1)
    exact = WZ / 2 * np.sqrt(np.log(s / d_th))
    got = hm.z_um[:, 5]
    np.testing.assert_allclose(got, exact, rtol=0, atol=2e-4)
    # relative dose modulation 2 exp(−π² w₀²/(4h²)) gives the ripple; spectrum peak at 1/h
    freq, amp = spectrum(got - got.mean(), grid.step_um[1])
    assert freq[np.argmax(amp[1:]) + 1] == pytest.approx(1 / h, rel=0.05)


def test_layer_ripple_of_a_side_wall() -> None:
    dz = 1.0  # dose modulation 2 exp(−π² w_z²/(4 Δz²)) ≈ 5.7 %
    zs = [k * dz for k in range(-6, 7)]
    grid = Grid(origin_um=(-0.55, -0.005, -2.0), step_um=(0.1, 0.01, 0.01), shape=(400, 80, 11))
    f = dose_field(lines([0.0], zs), grid, FOCUS)
    d0 = line_d0(20.0, 1e3)
    d_th = 0.5 * d0
    yw = wall_profile(f, d_th, x_um=0.0)
    z = grid.origin_um[2] + (np.arange(grid.shape[0]) + 0.5) * grid.step_um[2]
    t = np.exp(-4 * (z[:, None] - np.array(zs)[None, :]) ** 2 / WZ**2).sum(axis=1)
    exact = W0 / 2 * np.sqrt(np.log(d0 * t / d_th))
    np.testing.assert_allclose(yw, exact, rtol=0, atol=2e-4)
    freq, amp = spectrum(yw - yw.mean(), grid.step_um[2])
    assert freq[np.argmax(amp[1:]) + 1] == pytest.approx(1 / dz, rel=0.05)


def test_height_map_file_and_solid_field(tmp_path: Path) -> None:
    f = dose_field(lines([0.0], [0.0]), GRID, FOCUS)
    d_th = 0.3 * line_d0(20.0, 1e3)
    hm = height_map(f, d_th, material_below="IP-S", material_above="developer")
    hm.save(tmp_path / "top.json")
    back = HeightMap.load(tmp_path / "top.json")
    assert back.z_um.tobytes() == hm.z_um.tobytes()
    assert (back.material_below, back.material_above) == ("IP-S", "developer")
    assert np.isnan(hm.z_um[0, 0])  # no solid far from the line
    solid = solid_field(f, d_th, "IP-S")
    m: NDArray[np.uint8] = solid.data["material"]
    assert solid.data["materials"] == ["none", "IP-S"]
    assert m.dtype == np.uint8 and set(np.unique(m)) == {0, 1}
    assert solid.data["threshold_dose_mW2s_per_um4"] == d_th
