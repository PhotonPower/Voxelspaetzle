"""V5a: shrinkage with linear elasticity on voxel hexahedra (spezifikation §3.8)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray

from voxelspaetzle.dose import Grid, VolumeField
from voxelspaetzle.mechanics import Displacement, Elastic, deformed_height_map, solve_shrinkage
from voxelspaetzle.threshold import HeightMap

S = 0.01


def alpha_field(alpha: NDArray[np.float64], step: tuple[float, float, float]) -> VolumeField:
    nz, ny, nx = alpha.shape
    return VolumeField(Grid((0.0, 0.0, 0.0), step, (nz, ny, nx)), {"alpha": alpha})


def nodes(d: Displacement) -> NDArray[np.float64]:
    """Coordinates of the grid nodes (nz+1, ny+1, nx+1, 3) in µm."""
    g = d.grid
    x, y, z = (g.origin_um[k] + np.arange(g.shape[2 - k] + 1) * g.step_um[k] for k in range(3))
    zz, yy, xx = np.meshgrid(z, y, x, indexing="ij")
    return np.stack([xx, yy, zz], axis=-1)


def test_free_block_shrinks_homogeneously_patch_test() -> None:
    """Free body, homogeneous eigenstrain: stress free, u = −s (r − r₀) exactly."""
    a = np.ones((4, 6, 10))
    d = solve_shrinkage(alpha_field(a, (0.5, 0.4, 0.3)), Elastic(1000.0, 0.3, S), support="free")
    r0 = d.reference_um
    expected = -S * (nodes(d) - np.asarray(r0))
    err = np.abs(d.u_um - expected)[d.active].max()
    assert err < 1e-9 * S * 5.0


def test_free_voxel_sphere_with_staircase_and_partial_alpha() -> None:
    n = 16
    c = (np.arange(n) + 0.5) - n / 2
    zz, yy, xx = np.meshgrid(c, c, c, indexing="ij")
    a = np.where(xx**2 + yy**2 + zz**2 <= (n / 2 - 1) ** 2, 0.6, 0.0)
    d = solve_shrinkage(alpha_field(a, (1.0, 1.0, 1.0)), Elastic(1000.0, 0.3, S), support="free")
    expected = -0.6 * S * (nodes(d) - np.asarray(d.reference_um))
    assert np.abs(d.u_um - expected)[d.active].max() < 1e-9


def test_bonded_plate_centre_matches_constrained_shrinkage() -> None:
    """Thin film on a substrate: ε_zz = −s (1 + ν)/(1 − ν) away from the edges."""
    nu, t = 0.3, 4.0
    a = np.ones((4, 60, 60))
    d = solve_shrinkage(
        alpha_field(a, (1.0, 1.0, 1.0)),
        Elastic(1000.0, nu, S),
        support="substrate",
        substrate_z_um=0.0,
    )
    top_centre = d.u_um[4, 30, 30]
    assert top_centre[2] == pytest.approx(-S * t * (1 + nu) / (1 - nu), rel=1e-2)
    assert abs(top_centre[0]) < 1e-9 and abs(top_centre[1]) < 1e-9
    assert np.all(d.u_um[0][d.active[0]] == 0.0)  # clamped on the substrate


def test_displacement_does_not_depend_on_youngs_modulus() -> None:
    a = np.ones((3, 8, 8))
    f = alpha_field(a, (1.0, 1.0, 1.0))
    u1 = solve_shrinkage(f, Elastic(500.0, 0.25, S), "substrate", substrate_z_um=0.0).u_um
    u2 = solve_shrinkage(f, Elastic(4000.0, 0.25, S), "substrate", substrate_z_um=0.0).u_um
    np.testing.assert_allclose(u1, u2, rtol=0, atol=1e-10)


def test_developed_voxels_only_and_missing_support() -> None:
    a = np.zeros((4, 6, 6))
    a[1:3, 2:4, 2:4] = 1.0  # floating block, not on the substrate
    a[0, 0, 0] = 0.4  # below α_dev: developed away
    f = alpha_field(a, (1.0, 1.0, 1.0))
    with pytest.raises(ValueError, match="substrate"):
        solve_shrinkage(f, Elastic(1000.0, 0.3, S), "substrate", substrate_z_um=0.0)
    d = solve_shrinkage(f, Elastic(1000.0, 0.3, S), "free")
    assert d.active.sum() == 3 * 3 * 3


def test_interpolation_and_file_roundtrip(tmp_path: Path) -> None:
    a = np.ones((3, 4, 5))
    d = solve_shrinkage(alpha_field(a, (1.0, 1.0, 1.0)), Elastic(1000.0, 0.3, S), "free")
    p = np.array([[0.3, 1.7, 2.2], [4.0, 0.0, 3.0]])
    expected = -S * (p - np.asarray(d.reference_um))
    np.testing.assert_allclose(d.at(p), expected, atol=1e-12)
    d.save(tmp_path / "u.json")
    back = Displacement.load(tmp_path / "u.json")
    assert back.u_um.tobytes() == d.u_um.tobytes() and back.grid == d.grid


def test_deformed_height_map_of_the_bonded_plate() -> None:
    nu, t = 0.3, 4.0
    a = np.ones((4, 60, 60))
    d = solve_shrinkage(
        alpha_field(a, (1.0, 1.0, 1.0)), Elastic(1000.0, nu, S), "substrate", substrate_z_um=0.0
    )
    hm = HeightMap((0.5, 0.5), (1.0, 1.0), np.full((60, 60), t), "IP-S", "air")
    out = deformed_height_map(hm, d)
    assert out.z_um[30, 30] == pytest.approx(t * (1 - S * (1 + nu) / (1 - nu)), rel=1e-4)
