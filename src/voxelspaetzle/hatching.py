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


def _crossings(
    loops: Sequence[FloatArray], spacing_um: float, angle_rad: float, phase_um: float
) -> tuple[NDArray[np.int64], FloatArray]:
    """Line indices j and positions u along d of all edge crossings (half-open rule)."""
    d = np.array([np.cos(angle_rad), np.sin(angle_rad)])
    nrm = np.array([-d[1], d[0]])
    js, us = [np.zeros(0, dtype=np.int64)], [np.zeros(0)]
    for loop in loops:
        p = np.asarray(loop, dtype=np.float64)
        q = np.roll(p, -1, axis=0)
        u0, u1, v0, v1 = p @ d, q @ d, p @ nrm, q @ nrm
        lo, hi = np.minimum(v0, v1), np.maximum(v0, v1)
        jlo = np.floor((lo - phase_um) / spacing_um).astype(np.int64)
        jhi = np.ceil((hi - phase_um) / spacing_um).astype(np.int64)
        count = np.where(hi > lo, jhi - jlo + 1, 0)
        edge = np.repeat(np.arange(p.shape[0]), count)
        offset = np.arange(count.sum()) - np.repeat(np.cumsum(count) - count, count)
        j = np.repeat(jlo, count) + offset
        c = phase_um + j * spacing_um
        ok = (c >= lo[edge]) & (c < hi[edge])
        edge, j, c = edge[ok], j[ok], c[ok]
        t = (c - v0[edge]) / (v1[edge] - v0[edge])
        js.append(j)
        us.append(u0[edge] + t * (u1[edge] - u0[edge]))
    return np.concatenate(js), np.concatenate(us)


def line_intervals(
    loops: Sequence[FloatArray], spacing_um: float, angle_rad: float, phase_um: float
) -> tuple[NDArray[np.int64], FloatArray, FloatArray]:
    """Inside intervals [ua, ub] on the lines j (even–odd rule), sorted by (j, ua)."""
    j, u = _crossings(loops, spacing_um, angle_rad, phase_um)
    order = np.lexsort((u, j))
    j, u = j[order], u[order]
    if j.size:
        starts = np.flatnonzero(np.r_[True, j[1:] != j[:-1]])
        if np.any(np.diff(np.r_[starts, j.size]) % 2):
            raise ValueError("odd number of crossings: loops are open or self-intersecting")
    return j[0::2], u[0::2], u[1::2]


def _subtract(
    j: NDArray[np.int64],
    ua: FloatArray,
    ub: FloatArray,
    jx: NDArray[np.int64],
    xa: FloatArray,
    xb: FloatArray,
) -> tuple[NDArray[np.int64], FloatArray, FloatArray]:
    """Intervals (j, ua, ub) minus the intervals (jx, xa, xb) on the same lines."""
    if jx.size == 0:
        return j, ua, ub
    oj, oa, ob = [], [], []
    for line in np.unique(j):
        cuts = sorted(zip(xa[jx == line].tolist(), xb[jx == line].tolist(), strict=True))
        for a, b in zip(ua[j == line].tolist(), ub[j == line].tolist(), strict=True):
            for ca, cb in cuts:
                if cb <= a or ca >= b:
                    continue
                if ca > a:
                    oj.append(line)
                    oa.append(a)
                    ob.append(ca)
                a = max(a, cb)
                if a >= b:
                    break
            if a < b:
                oj.append(line)
                oa.append(a)
                ob.append(b)
    return np.array(oj, dtype=np.int64), np.array(oa), np.array(ob)


def common_length(
    j: NDArray[np.int64],
    ua: FloatArray,
    ub: FloatArray,
    jx: NDArray[np.int64],
    xa: FloatArray,
    xb: FloatArray,
) -> float:
    """Total length common to the intervals (j, ua, ub) and (jx, xa, xb) on the same lines."""
    total = 0.0
    for line in np.intersect1d(j, jx):
        for a, b in zip(ua[j == line].tolist(), ub[j == line].tolist(), strict=True):
            lo = np.maximum(a, xa[jx == line])
            hi = np.minimum(b, xb[jx == line])
            total += float(np.clip(hi - lo, 0.0, None).sum())
    return total


def inside_loops(points: FloatArray, loops: Sequence[FloatArray]) -> NDArray[np.bool_]:
    """Even–odd point-in-polygon test for points (N, 2) against all loops together."""
    pts = np.asarray(points, dtype=np.float64).reshape(-1, 2)
    inside = np.zeros(pts.shape[0], dtype=bool)
    for loop in loops:
        p = np.asarray(loop, dtype=np.float64)
        q = np.roll(p, -1, axis=0)
        y = pts[:, 1:2]
        crosses = (p[:, 1] <= y) != (q[:, 1] <= y)
        with np.errstate(divide="ignore", invalid="ignore"):
            xc = p[:, 0] + (y - p[:, 1]) * (q[:, 0] - p[:, 0]) / (q[:, 1] - p[:, 1])
        inside ^= (np.count_nonzero(crosses & (pts[:, 0:1] < xc), axis=1) % 2).astype(bool)
    return inside


def hatch_loops(
    loops: Sequence[FloatArray],
    spacing_um: float,
    angle_rad: float = 0.0,
    phase_um: float | None = None,
    serpentine: bool = True,
    exclude: Sequence[FloatArray] = (),
) -> FloatArray:
    """Hatch lines inside the loops, as segments (M, 2, 2) of (start, end) in µm.

    Lines run along d = (cos a, sin a) at the offsets c_j = phase + j·spacing along the normal
    (−sin a, cos a), a global grid anchored at the origin (default phase = spacing/2). An edge
    from v0 to v1 (normal coordinate) crosses line c if c lies in the half-open interval
    [min, max); edges along a line and vertices on a line are thus counted consistently and no
    zero-length segments arise. Intervals inside ``exclude`` (loops of bodies written earlier,
    §3.11) are removed on the same grid. Segments are ordered by line, along d within a line;
    with ``serpentine`` every second line runs backwards.
    """
    if not spacing_um > 0.0:
        raise ValueError("spacing_um must be positive")
    phase = 0.5 * spacing_um if phase_um is None else float(phase_um)
    d = np.array([np.cos(angle_rad), np.sin(angle_rad)])
    nrm = np.array([-d[1], d[0]])
    jj, ua, ub = line_intervals(loops, spacing_um, angle_rad, phase)
    if len(exclude):
        jj, ua, ub = _subtract(jj, ua, ub, *line_intervals(exclude, spacing_um, angle_rad, phase))
    if jj.size == 0:
        return np.zeros((0, 2, 2))
    keep = ub - ua > 1e-12 * max(1.0, float(np.max(np.abs(np.r_[ua, ub]))))
    ua, ub, jj = ua[keep], ub[keep], jj[keep]
    if serpentine:
        lines = np.unique(jj)
        back = np.searchsorted(lines, jj) % 2 == 1
        ua, ub = np.where(back, ub, ua), np.where(back, ua, ub)
        # within a backwards line the segments are visited in reverse order
        key = np.where(back, -np.minimum(ua, ub), np.minimum(ua, ub))
        o = np.lexsort((key, jj))
        ua, ub, jj = ua[o], ub[o], jj[o]
    c = phase + jj * spacing_um
    start = ua[:, None] * d + c[:, None] * nrm
    end = ub[:, None] * d + c[:, None] * nrm
    return np.stack([start, end], axis=1)
