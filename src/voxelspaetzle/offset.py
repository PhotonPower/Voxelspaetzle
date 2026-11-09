"""Inward offsets of section loops for contours and the hatch region (spezifikation §3.9).

Loops are closed polygons (N, 2) in µm with the solid on the left (outer loops counter-clockwise,
holes clockwise). Every edge line is moved by δ to its left, i.e. into the solid; consecutive
lines meet at their intersection (miter). Edges whose offset runs against the original direction
have collapsed and are removed, repeatedly; loops with fewer than three edges left, a reversed
orientation or holes no longer inside an outer loop vanish. Intersections that this local
cleanup cannot resolve (e.g. two arms of a C coming within 2δ) raise ``ValueError``.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

from voxelspaetzle.hatching import inside_loops, polygon_area

FloatArray = NDArray[np.float64]
_PARALLEL = 1e-12


def _cross(a: FloatArray, b: FloatArray) -> FloatArray:
    out: FloatArray = a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]
    return out


def _offset_one(loop: FloatArray, delta: float) -> FloatArray | None:
    """Miter offset of one loop with removal of collapsed edges; None if it vanishes."""
    p = np.asarray(loop, dtype=np.float64)
    e = np.roll(p, -1, axis=0) - p
    length = np.linalg.norm(e, axis=1)
    keep = length > 0.0
    p, e, length = p[keep], e[keep], length[keep]
    d = e / length[:, None]
    n = np.column_stack([-d[:, 1], d[:, 0]])  # left normal, into the solid
    a = p + delta * n  # a point on each offset line
    active = np.arange(p.shape[0])
    while True:
        if active.size < 3:
            return None
        prev = np.roll(active, 1)
        dp, dc = d[prev], d[active]
        den = _cross(dp, dc)
        # vertex where line prev meets line active: a_prev + s·d_prev = a_act + t·d_act
        s = _cross(a[active] - a[prev], dc) / np.where(np.abs(den) > _PARALLEL, den, 1.0)
        v = a[prev] + s[:, None] * dp
        parallel = np.abs(den) <= _PARALLEL
        same = parallel & (np.einsum("ij,ij->i", dp, dc) > 0.0)
        # collinear neighbours: vertex at the foot of the original vertex on the offset line
        v[same] = a[active[same]]
        # antiparallel neighbours: the material between them is gone if their gap is negative
        anti = parallel & ~same
        gap = np.einsum("ij,ij->i", a[active] - a[prev], n[prev])
        dead = np.zeros(active.size, dtype=bool)
        dead |= anti & (gap <= 0.0)
        dead |= np.roll(anti & (gap <= 0.0), -1)
        v[anti] = 0.5 * (a[prev[anti]] + a[active[anti]])
        # edge of line active runs from v[k] to v[k+1]
        step = np.roll(v, -1, axis=0) - v
        dead |= np.einsum("ij,ij->i", step, dc) < 0.0
        if not dead.any():
            break
        active = active[~dead]
    out: FloatArray = v
    if np.sign(polygon_area(out)) != np.sign(polygon_area(p)) or polygon_area(out) == 0.0:
        return None
    return out


def _segments_intersect(loops: Sequence[FloatArray]) -> NDArray[np.float64] | None:
    """A point where two non-adjacent edges of the loops cross, or None (x-sweep)."""
    starts, ends, owner, idx = [], [], [], []
    for k, lp in enumerate(loops):
        starts.append(lp)
        ends.append(np.roll(lp, -1, axis=0))
        owner.append(np.full(lp.shape[0], k))
        idx.append(np.arange(lp.shape[0]))
    s, t = np.concatenate(starts), np.concatenate(ends)
    own, ix = np.concatenate(owner), np.concatenate(idx)
    size = np.array([lp.shape[0] for lp in loops])[own]
    xlo, xhi = np.minimum(s[:, 0], t[:, 0]), np.maximum(s[:, 0], t[:, 0])
    order = np.argsort(xlo)
    s, t, own, ix, size, xlo, xhi = (a[order] for a in (s, t, own, ix, size, xlo, xhi))
    stop = np.searchsorted(xlo, xhi, side="right")
    count = np.maximum(stop - np.arange(s.shape[0]) - 1, 0)
    total = int(count.sum())
    chunk = 1 << 22
    first = np.repeat(np.arange(s.shape[0]), count)
    offset = np.arange(total) - np.repeat(np.cumsum(count) - count, count)
    second = first + 1 + offset
    for c0 in range(0, total, chunk):
        a, b = first[c0 : c0 + chunk], second[c0 : c0 + chunk]
        same = own[a] == own[b]
        diff = (ix[b] - ix[a]) % size[a]
        keep = ~(same & ((diff == 1) | (diff == size[a] - 1)))
        keep &= (np.maximum(s[a, 1], t[a, 1]) >= np.minimum(s[b, 1], t[b, 1])) & (
            np.maximum(s[b, 1], t[b, 1]) >= np.minimum(s[a, 1], t[a, 1])
        )
        a, b = a[keep], b[keep]
        if a.size == 0:
            continue
        r, q, w = t[a] - s[a], t[b] - s[b], s[b] - s[a]
        den = _cross(r, q)
        ok = np.abs(den) > _PARALLEL
        u = _cross(w, q) / np.where(ok, den, 1.0)
        v = _cross(w, r) / np.where(ok, den, 1.0)
        hit = ok & (u > 1e-12) & (u < 1 - 1e-12) & (v > 1e-12) & (v < 1 - 1e-12)
        if hit.any():
            k = int(np.flatnonzero(hit)[0])
            out: FloatArray = s[a[k]] + u[k] * r[k]
            return out
    return None


def offset_loops(loops: Sequence[FloatArray], delta_um: float) -> list[FloatArray]:
    """Loops moved by ``delta_um`` ≥ 0 into the solid (§3.9); vanished loops are dropped."""
    if delta_um < 0.0:
        raise ValueError("delta_um must not be negative")
    if delta_um == 0.0:
        return [np.asarray(lp, dtype=np.float64) for lp in loops]
    out = [r for r in (_offset_one(lp, delta_um) for lp in loops) if r is not None]
    # holes must lie inside an outer loop, outer loops must not lie inside a hole
    changed = True
    while changed and out:
        changed = False
        outer = [lp for lp in out if polygon_area(lp) > 0.0]
        holes = [lp for lp in out if polygon_area(lp) < 0.0]
        for lp in out:
            pt = lp[:1]
            if polygon_area(lp) < 0.0 and not inside_loops(pt, outer)[0]:
                out = [x for x in out if x is not lp]
                changed = True
                break
            if polygon_area(lp) > 0.0 and holes and inside_loops(pt, holes)[0]:
                if not inside_loops(pt, [x for x in outer if x is not lp])[0]:
                    out = [x for x in out if x is not lp]
                    changed = True
                    break
    if out:
        hit = _segments_intersect(out)
        if hit is not None:
            raise ValueError(
                f"offset loops intersect near ({hit[0]:.4g}, {hit[1]:.4g}) µm: a feature is "
                f"narrower than twice the offset {delta_um} µm and is not resolved"
            )
    return out
