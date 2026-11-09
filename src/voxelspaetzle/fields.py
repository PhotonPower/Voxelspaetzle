"""Writing fields (spezifikation §3.10): grid, splitting at boundaries, field table and order."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise
from typing import Any

import numpy as np
from numpy.typing import NDArray

from voxelspaetzle.path import KIND_POINT, SINGLE_FIELD, Segments

_MERGE_T = 1e-12


@dataclass(frozen=True)
class FieldGrid:
    """Square writing fields of edge ``size_xy_um`` and height blocks of ``size_z_um``.

    Field (i, j) covers x ∈ [ox + (i − ½)s, ox + (i + ½)s) and likewise y, so the field centres
    (stage positions) lie on the grid ox + i·s. Height block k covers z ∈ [oz + k·s_z,
    oz + (k + 1)·s_z); with s_z = ∞ there is a single block. All lengths in µm.
    """

    size_xy_um: float
    size_z_um: float = math.inf
    origin_um: tuple[float, float, float] = (0.0, 0.0, 0.0)

    def __post_init__(self) -> None:
        if not (self.size_xy_um > 0.0 and self.size_z_um > 0.0):
            raise ValueError("field sizes must be positive")

    def index_of(self, points_um: NDArray[np.float64]) -> NDArray[np.int64]:
        """Field index (i, j, k) of points (N, 3)."""
        p = np.asarray(points_um, dtype=np.float64).reshape(-1, 3)
        o = np.asarray(self.origin_um)
        ij = np.floor((p[:, :2] - o[:2]) / self.size_xy_um + 0.5).astype(np.int64)
        if math.isinf(self.size_z_um):
            k = np.zeros((p.shape[0], 1), dtype=np.int64)
        else:
            k = np.floor((p[:, 2:3] - o[2]) / self.size_z_um).astype(np.int64)
        return np.hstack([ij, k])

    def center_of(self, index: Sequence[int]) -> tuple[float, float, float]:
        """Stage position of field (i, j, k): xy centre of the field, z centre of the block."""
        i, j, k = (int(v) for v in index)
        ox, oy, oz = self.origin_um
        z = oz if math.isinf(self.size_z_um) else oz + (k + 0.5) * self.size_z_um
        return (ox + i * self.size_xy_um, oy + j * self.size_xy_um, z)

    def bounds_of(self, index: Sequence[int]) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Lower and upper corner of field (i, j, k) (upper bound exclusive)."""
        i, j, k = (int(v) for v in index)
        s, (ox, oy, oz) = self.size_xy_um, self.origin_um
        lo = [ox + (i - 0.5) * s, oy + (j - 0.5) * s, -math.inf]
        hi = [ox + (i + 0.5) * s, oy + (j + 0.5) * s, math.inf]
        if not math.isinf(self.size_z_um):
            lo[2], hi[2] = oz + k * self.size_z_um, oz + (k + 1) * self.size_z_um
        return np.array(lo), np.array(hi)


def _split_one(a: NDArray[np.float64], b: NDArray[np.float64], g: FieldGrid) -> list[float]:
    """Parameters t ∈ (0, 1) where the segment a → b crosses field boundaries in x or y."""
    ts: list[float] = []
    for ax in (0, 1):
        o, da = g.origin_um[ax], b[ax] - a[ax]
        if da == 0.0:
            continue
        i0 = math.floor((a[ax] - o) / g.size_xy_um + 0.5)
        i1 = math.floor((b[ax] - o) / g.size_xy_um + 0.5)
        for i in range(min(i0, i1), max(i0, i1)):
            t = (o + (i + 0.5) * g.size_xy_um - a[ax]) / da
            if 0.0 < t < 1.0:
                ts.append(t)
    ts.sort()
    merged: list[float] = []
    for t in ts:
        if not merged or t - merged[-1] > _MERGE_T:
            merged.append(t)
    return merged


def _split_layer(s: Segments, g: FieldGrid) -> tuple[Segments, NDArray[np.int64]]:
    """Segments split at the field boundaries and the field index (i, j, k) of each piece."""
    ia, ib = g.index_of(s.start_um), g.index_of(s.end_um)
    cross = np.any(ia != ib, axis=1) & (s.kind != KIND_POINT)
    if not np.any(cross):
        return s, ia
    rows: list[int] = []
    starts: list[NDArray[np.float64]] = []
    ends: list[NDArray[np.float64]] = []
    for n in range(s.n):
        a, b = s.start_um[n], s.end_um[n]
        ts = [0.0, *_split_one(a, b, g), 1.0] if cross[n] else [0.0, 1.0]
        for t0, t1 in pairwise(ts):
            rows.append(n)
            starts.append(a if t0 == 0.0 else a + t0 * (b - a))
            ends.append(b if t1 == 1.0 else a + t1 * (b - a))
    r = np.array(rows)
    st, en = np.array(starts), np.array(ends)
    out = Segments(
        st, en, s.power_mW[r], s.speed_um_per_s[r], s.kind[r], s.dwell_s[r], s.region[r], s.field[r]
    )
    return out, g.index_of(0.5 * (st + en))


def _key(row: NDArray[np.int64]) -> tuple[int, int, int]:
    return (int(row[0]), int(row[1]), int(row[2]))


def field_order(indices: set[tuple[int, int, int]]) -> list[tuple[int, int, int]]:
    """Writing order: height blocks k upwards, rows j upwards, i alternating per row."""
    order: list[tuple[int, int, int]] = []
    for k in sorted({ix[2] for ix in indices}):
        rows = sorted({ix[1] for ix in indices if ix[2] == k})
        for r, j in enumerate(rows):
            cols = sorted(ix[0] for ix in indices if ix[2] == k and ix[1] == j)
            order.extend((i, j, k) for i in (cols if r % 2 == 0 else cols[::-1]))
    return order


def assign_fields(
    layers: Sequence[Segments], z_um: Sequence[float], grid: FieldGrid | None
) -> tuple[list[Segments], list[dict[str, Any]]]:
    """Split the segments of all layers at field boundaries and number the fields.

    Returns the new segments per layer (``field`` = index into the table) and the field table in
    writing order. Without a grid everything lies in one field at the origin.
    """
    if grid is None:
        out = [
            Segments(
                s.start_um,
                s.end_um,
                s.power_mW,
                s.speed_um_per_s,
                s.kind,
                s.dwell_s,
                s.region,
                np.zeros(s.n, dtype=np.int32),
            )
            for s in layers
        ]
        return out, [dict(SINGLE_FIELD)]
    split = []
    for s, z in zip(layers, z_um, strict=True):
        pieces, idx = _split_layer(s, grid)
        idx[:, 2] = grid.index_of(np.array([[0.0, 0.0, z]]))[0, 2]
        split.append((pieces, idx))
    order = field_order({_key(row) for _, idx in split for row in idx})
    number = {ix: n for n, ix in enumerate(order)}
    out = []
    for pieces, idx in split:
        pieces.field = np.array([number[_key(row)] for row in idx], dtype=np.int32)
        out.append(pieces)
    table = [{"index": list(ix), "center_um": list(grid.center_of(ix))} for ix in order]
    return out, table
