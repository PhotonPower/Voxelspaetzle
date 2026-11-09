"""Layer heights and planar sections of B-rep bodies via Nurbforge (spezifikation §3.1)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import nurbforge as nf
from numpy.typing import NDArray

from voxelspaetzle.hatching import polygon_area

FloatArray = NDArray[np.float64]
_MAX_SAMPLES = 1 << 20


def slice_heights(
    z_min_um: float,
    z_max_um: float,
    slicing_um: float,
    critical: Sequence[float] = (),
    eps_um: float = 1e-6,
) -> FloatArray:
    """Layer heights z_k = z_min + (k + ½)·Δz below z_max (midpoint rule, §3.1).

    A height closer than ``eps_um`` to a critical height of the body (vertex, planar face,
    height extremum) is moved up to that height plus ``eps_um``; a section is never taken on a
    critical height. Heights at or above z_max are dropped.
    """
    if not slicing_um > 0.0:
        raise ValueError("slicing_um must be positive")
    k = np.arange(int(np.ceil((z_max_um - z_min_um) / slicing_um)) + 1)
    z = z_min_um + (k + 0.5) * slicing_um
    for c in critical:
        z = np.where(np.abs(z - c) < eps_um, c + eps_um, z)
    return np.asarray(z[z < z_max_um], dtype=np.float64)


def body_z_range(shell: Any) -> tuple[float, float, list[float]]:
    """Lowest and highest point of a closed shell along z and all its critical heights."""
    hs = [float(h) for h in nf.critical_heights(shell, (0.0, 0.0, 1.0))]
    if not hs:
        raise ValueError("shell has no critical heights along z")
    return min(hs), max(hs), hs


def _sample_curve(curve: Any, chord_tol_um: float) -> FloatArray:
    """Uniform parameter samples, doubled until the sagitta at parameter midpoints ≤ tol."""
    n = 17
    p = np.asarray(curve.sample(n), dtype=np.float64)
    while True:
        q = np.asarray(curve.sample(2 * n - 1), dtype=np.float64)
        dev = np.linalg.norm(q[1::2] - 0.5 * (p[:-1] + p[1:]), axis=1).max()
        if dev <= chord_tol_um or 2 * n - 1 > _MAX_SAMPLES:
            return q
        n, p = 2 * n - 1, q


def section_loops(shell: Any, z_um: float, chord_tol_um: float = 1e-3) -> list[FloatArray]:
    """Closed polygons (N, 2) in µm of the section of ``shell`` with the plane z = z_um.

    Each loop of Nurbforge's ``section`` (solid on the left: outer counter-clockwise, holes
    clockwise seen from +z) is sampled curve by curve in 3D with chord deviation ≤
    ``chord_tol_um``; the orientation is checked against the signed loop area from Nurbforge.
    """
    sec = nf.section(shell, nf.Plane((0.0, 0.0, float(z_um)), (0.0, 0.0, 1.0)))
    loops = []
    for loop in sec.loops:
        pts = [_sample_curve(c.curve3d, chord_tol_um)[:-1, :2] for c in loop.curves]
        poly = np.concatenate(pts, axis=0)
        if np.sign(polygon_area(poly)) != np.sign(float(loop.area)):
            raise ValueError("section loop orientation differs from Nurbforge's signed area")
        loops.append(poly)
    return loops
