"""Hatching of planar polygon loops (spezifikation §3.9).

Loops are closed polygons (N, 2) in µm; outer loops counter-clockwise, holes clockwise (as from
Nurbforge ``section``). Inside is decided by the even–odd rule along each line, which coincides
with the orientation rule for non-overlapping loops.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


def polygon_area(loop: FloatArray) -> float:
    """Signed area (µm²) by the shoelace formula; positive for counter-clockwise loops."""
    x, y = loop[:, 0], loop[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(np.roll(x, -1), y))


def polygon_perimeter(loop: FloatArray) -> float:
    """Length (µm) of the closed polygon."""
    return float(np.linalg.norm(np.roll(loop, -1, axis=0) - loop, axis=1).sum())


def hatch_loops(
    loops: Sequence[FloatArray],
    spacing_um: float,
    angle_rad: float = 0.0,
    phase_um: float | None = None,
    serpentine: bool = True,
) -> FloatArray:
    """Hatch lines inside the loops, as segments (M, 2, 2) of (start, end) in µm.

    Lines run along d = (cos a, sin a) at the offsets c_j = phase + j·spacing along the normal
    (−sin a, cos a), a global grid anchored at the origin (default phase = spacing/2). An edge
    from v0 to v1 (normal coordinate) crosses line c if c lies in the half-open interval
    [min, max); edges along a line and vertices on a line are thus counted consistently and no
    zero-length segments arise. Segments are ordered by line, along d within a line; with
    ``serpentine`` every second line runs backwards.
    """
    if not spacing_um > 0.0:
        raise ValueError("spacing_um must be positive")
    phase = 0.5 * spacing_um if phase_um is None else float(phase_um)
    d = np.array([np.cos(angle_rad), np.sin(angle_rad)])
    nrm = np.array([-d[1], d[0]])
    js, us = [], []
    for loop in loops:
        p = np.asarray(loop, dtype=np.float64)
        q = np.roll(p, -1, axis=0)
        u0, u1, v0, v1 = p @ d, q @ d, p @ nrm, q @ nrm
        lo, hi = np.minimum(v0, v1), np.maximum(v0, v1)
        jlo = np.floor((lo - phase) / spacing_um).astype(np.int64)
        jhi = np.ceil((hi - phase) / spacing_um).astype(np.int64)
        count = np.where(hi > lo, jhi - jlo + 1, 0)
        edge = np.repeat(np.arange(p.shape[0]), count)
        j = np.repeat(jlo, count) + (
            np.arange(count.sum()) - np.repeat(np.cumsum(count) - count, count)
        )
        c = phase + j * spacing_um
        ok = (c >= lo[edge]) & (c < hi[edge])
        edge, j, c = edge[ok], j[ok], c[ok]
        t = (c - v0[edge]) / (v1[edge] - v0[edge])
        js.append(j)
        us.append(u0[edge] + t * (u1[edge] - u0[edge]))
    if not js or sum(a.size for a in js) == 0:
        return np.zeros((0, 2, 2))
    j_all, u_all = np.concatenate(js), np.concatenate(us)
    order = np.lexsort((u_all, j_all))
    j_all, u_all = j_all[order], u_all[order]
    starts = np.flatnonzero(np.r_[True, j_all[1:] != j_all[:-1]])
    sizes = np.diff(np.r_[starts, j_all.size])
    if np.any(sizes % 2):
        raise ValueError("odd number of crossings: loops are open or self-intersecting")
    ua, ub, jj = u_all[0::2], u_all[1::2], j_all[0::2]
    keep = ub - ua > 1e-12 * max(1.0, float(np.max(np.abs(u_all))))
    ua, ub, jj = ua[keep], ub[keep], jj[keep]
    if serpentine:
        lines = np.unique(jj)
        rank = np.searchsorted(lines, jj)
        back = rank % 2 == 1
        ua, ub = np.where(back, ub, ua), np.where(back, ua, ub)
        # within a backwards line the segments are visited in reverse order
        key = np.where(back, -np.minimum(ua, ub), np.minimum(ua, ub))
        o = np.lexsort((key, jj))
        ua, ub, jj = ua[o], ub[o], jj[o]
    c = phase + jj * spacing_um
    start = ua[:, None] * d + c[:, None] * nrm
    end = ub[:, None] * d + c[:, None] * nrm
    return np.stack([start, end], axis=1)
