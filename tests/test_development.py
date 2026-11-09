"""P16: developer access, enclosed liquid resist (spezifikation §3.8)."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from voxelspaetzle.development import trapped_liquid
from voxelspaetzle.dose import Grid, VolumeField


def field(alpha: NDArray[np.float64]) -> VolumeField:
    nz, ny, nx = alpha.shape
    return VolumeField(Grid((0.0, 0.0, 0.0), (1.0, 1.0, 1.0), (nz, ny, nx)), {"alpha": alpha})


def ball(
    n: int, r_out: float, r_in: float | None, centre_z: float | None = None
) -> NDArray[np.float64]:
    """Spherical shell r_in < r ≤ r_out (full ball for r_in = None) on voxel centres."""
    c = np.arange(n) + 0.5
    cz = n / 2 if centre_z is None else centre_z
    zz, yy, xx = np.meshgrid(c - cz, c - n / 2, c - n / 2, indexing="ij")
    r2 = xx**2 + yy**2 + zz**2
    inner = r2 > r_in**2 if r_in is not None else np.ones_like(r2, dtype=bool)
    out: NDArray[np.float64] = ((r2 <= r_out**2) & inner).astype(float)
    return out


def test_hollow_sphere_traps_its_cavity() -> None:
    a = ball(24, 10.0, 7.0)
    trapped = trapped_liquid(field(a), substrate=False)
    cavity = ball(24, 7.0, None) > 0  # all voxels inside the inner radius
    assert np.array_equal(trapped, cavity)


def test_development_hole_frees_the_cavity() -> None:
    a = ball(24, 10.0, 7.0)
    a[12:, 11:13, 11:13] = 0.0  # vertical channel from the cavity through the top shell
    assert not trapped_liquid(field(a), substrate=False).any()


def test_dome_on_the_substrate_traps_liquid_unless_it_has_a_hole() -> None:
    a = ball(24, 10.0, 7.0, centre_z=0.0)  # hemispherical shell standing on z = 0
    trapped = trapped_liquid(field(a), substrate=True)
    assert trapped.sum() == (ball(24, 7.0, None, centre_z=0.0) > 0).sum()
    assert not trapped_liquid(
        field(a), substrate=False
    ).any()  # open towards z < 0 without substrate
    a[0:2, 11:13, :] = 0.0  # slot through the foot of the shell
    assert not trapped_liquid(field(a), substrate=True).any()


def test_open_cup_and_partial_alpha() -> None:
    a = np.zeros((10, 12, 12))
    a[0, 1:11, 1:11] = 1.0
    a[:, 1:11, 1] = a[:, 1:11, 10] = a[:, 1, 1:11] = a[:, 10, 1:11] = 1.0
    assert not trapped_liquid(field(a), substrate=True).any()
    a[9, 1:11, 1:11] = 0.4  # lid below α_dev is developed away: still open
    assert not trapped_liquid(field(a), substrate=True).any()
    a[9, 1:11, 1:11] = 0.9  # solid lid closes the box
    assert trapped_liquid(field(a), substrate=True).sum() == 8 * 8 * 8
