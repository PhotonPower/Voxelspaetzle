"""V6a: outputs to the framework (spezifikation §3.12, §5.4)."""

from __future__ import annotations

import math
from collections import Counter
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray

from voxelspaetzle.dose import Grid, VolumeField
from voxelspaetzle.export import (
    bwpm_structure,
    fourier_grating_layers,
    read_stl,
    surface_triangles,
    transmission_along_z,
    write_stl,
)

STEP = (0.1, 0.1, 0.05)


def optical(n: NDArray[np.float64], kappa: NDArray[np.float64], lam: float) -> VolumeField:
    nz, ny, nx = n.shape
    return VolumeField(
        Grid((0.0, 0.0, 0.0), STEP, (nz, ny, nx)),
        {"n": n[None], "kappa": kappa[None], "wavelengths_um": [lam], "kappa_missing_um": []},
    )


def test_bwpm_two_materials_exact() -> None:
    n = np.ones((4, 5, 6))
    n[1:3, 1:4, 2:5] = 1.5051
    k = np.where(n > 1.0, 6.2e-5, 0.0)
    s = bwpm_structure(optical(n, k, 0.78), 0.78, index_before=1.0)
    assert s.indices == (1.0 + 0j, 1.5051 + 6.2e-5j)
    assert s.labels.shape == (4, 5, 6) and s.labels.dtype == np.int32
    np.testing.assert_array_equal(s.labels, (n > 1.0).astype(np.int32))
    assert (s.dx, s.dy, s.dz) == pytest.approx((1e-4, 1e-4, 5e-5))  # mm
    assert s.max_index_error == 0.0


def test_bwpm_gradient_is_quantised_with_bounded_error() -> None:
    n = np.broadcast_to(np.linspace(1.50, 1.52, 101)[None, None, :], (2, 3, 101)).copy()
    k = np.zeros_like(n)
    s = bwpm_structure(optical(n, k, 0.6), 0.6, index_before=1.5, max_levels=8)
    assert len(s.indices) == 8
    assert s.max_index_error <= 0.02 / 16 + 1e-15
    got = np.array(s.indices)[s.labels].real
    assert np.abs(got - n).max() == pytest.approx(s.max_index_error, abs=1e-15)
    finer = bwpm_structure(optical(n, k, 0.6), 0.6, index_before=1.5, max_levels=32)
    assert finer.max_index_error < s.max_index_error / 3


def test_bwpm_refuses_missing_absorption() -> None:
    n = np.full((2, 2, 2), 1.5)
    k = np.full((2, 2, 2), np.nan)
    with pytest.raises(ValueError, match="kappa"):
        bwpm_structure(optical(n, k, 0.55), 0.55, index_before=1.0)


def sawtooth(nx: int, nz: int) -> NDArray[np.float64]:
    """Voxelised blazed profile over one period: height grows linearly with x."""
    a = np.zeros((nz, 1, nx))
    for i in range(nx):
        a[: (i * nz) // nx + 1, 0, i] = 1.0
    return a


def test_fourier_grating_layers_of_a_voxel_sawtooth() -> None:
    nx, nz = 20, 10
    a = sawtooth(nx, nz)
    f = VolumeField(Grid((0.0, 0.0, 0.0), (0.05, 0.05, 0.02), (nz, 1, nx)), {"alpha": a})
    period, layers = fourier_grating_layers(f, y_index=0, solid="IP-Dip", background="air")
    assert period == pytest.approx(1.0)
    assert sum(ly["thickness_um"] for ly in layers) == pytest.approx(nz * 0.02)
    for ly in layers:
        assert ly["type"] == "lamellar1d"
        bp = ly["breakpoints_um"]
        assert bp[0] == 0.0 and bp[-1] == pytest.approx(period)
        assert len(ly["materials"]) == len(bp) - 1
    # fill factor of each voxel layer is kept
    z = 0
    for ly in layers:
        reps = round(ly["thickness_um"] / 0.02)
        bp, mats = ly["breakpoints_um"], ly["materials"]
        fill = sum(b - a_ for a_, b, m in zip(bp[:-1], bp[1:], mats, strict=True) if m == "IP-Dip")
        for kz in range(z, z + reps):
            assert fill == pytest.approx(a[kz, 0].sum() * 0.05)
        z += reps
    assert z == nz


def test_identical_rows_are_merged() -> None:
    a = np.zeros((6, 1, 10))
    a[:4, 0, 2:7] = 1.0
    f = VolumeField(Grid((0.0, 0.0, 0.0), (0.1, 0.1, 0.1), (6, 1, 10)), {"alpha": a})
    _, layers = fourier_grating_layers(f, 0, "IP-S", "air")
    assert [round(ly["thickness_um"], 12) for ly in layers] == [0.4, 0.2]
    assert layers[0]["breakpoints_um"] == pytest.approx([0.0, 0.2, 0.7, 1.0])
    assert layers[0]["materials"] == ["air", "IP-S", "air"]
    assert layers[1]["materials"] == ["air"]


def test_stl_is_watertight_and_keeps_the_volume(tmp_path: Path) -> None:
    n = 12
    c = np.arange(n) + 0.5 - n / 2
    zz, yy, xx = np.meshgrid(c, c, c, indexing="ij")
    r2 = xx**2 + yy**2 + zz**2
    a = ((r2 <= 25) & (r2 > 9)).astype(float)  # hollow sphere
    f = VolumeField(Grid((0.0, 0.0, 0.0), (0.2, 0.3, 0.4), (n, n, n)), {"alpha": a})
    path = tmp_path / "part.stl"
    write_stl(f, path)
    tri = read_stl(path)
    edges: Counter[tuple[tuple[float, ...], ...]] = Counter()
    for t in tri:
        for i in range(3):
            e = tuple(sorted((tuple(t[i]), tuple(t[(i + 1) % 3]))))
            edges[e] += 1
    assert set(edges.values()) == {2}  # every edge shared by exactly two triangles
    exact = a.sum() * 0.2 * 0.3 * 0.4

    def volume(t: NDArray[np.float64]) -> float:
        return float(np.einsum("ij,ij->i", t[:, 0], np.cross(t[:, 1], t[:, 2])).sum() / 6.0)

    assert volume(surface_triangles(f)) == pytest.approx(exact, rel=1e-12)
    assert volume(tri) == pytest.approx(exact, rel=1e-6)  # STL stores float32


def test_transmission_through_an_ip_black_slab() -> None:
    n = np.full((40, 2, 2), 1.5051)
    kappa = np.full_like(n, 1.0 * 0.78e-3 / (4 * math.pi))  # α = 1/mm
    t = transmission_along_z(optical(n, kappa, 0.78), 0.78)
    assert t.shape == (2, 2)
    np.testing.assert_allclose(t, math.exp(-1.0 * 40 * 0.05e-3), rtol=1e-12)
