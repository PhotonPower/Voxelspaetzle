"""Writing fields (spezifikation §3.10): splitting at field boundaries, field table and order."""

from __future__ import annotations

import math

import numpy as np
import pytest
from bodies import Cylinder

from voxelspaetzle.fields import FieldGrid, assign_fields
from voxelspaetzle.path import KIND_HATCH, Segments
from voxelspaetzle.slicer import WriteParameters, hatched_volume_um3, slice_shell

GRID = FieldGrid(size_xy_um=100.0, size_z_um=1.0)


def seg(a: tuple[float, float, float], b: tuple[float, float, float]) -> Segments:
    one = np.ones(1)
    return Segments(
        np.array([a]),
        np.array([b]),
        10.0 * one,
        1e4 * one,
        np.full(1, KIND_HATCH, dtype=np.int8),
        0.0 * one,
        np.zeros(1, dtype=np.int32),
        np.zeros(1, dtype=np.int32),
    )


def test_point_to_field_is_half_open() -> None:
    idx = GRID.index_of(np.array([[49.999, 0, 0.5], [50.0, 0, 0.5], [-50.0, -150.0, 1.0]]))
    assert idx.tolist() == [[0, 0, 0], [1, 0, 0], [0, -1, 1]]
    assert GRID.center_of((1, -1, 2)) == pytest.approx((100.0, -100.0, 2.5))


def test_segment_split_at_two_boundaries() -> None:
    s = seg((-80.0, 10.0, 0.5), (130.0, 10.0, 0.5))
    out, table = assign_fields([s], [0.5], GRID)
    o = out[0]
    assert o.n == 3
    np.testing.assert_allclose(o.start_um[:, 0], [-80.0, -50.0, 50.0])
    np.testing.assert_allclose(o.end_um[:, 0], [-50.0, 50.0, 130.0])
    assert [tuple(table[f]["index"]) for f in o.field] == [(-1, 0, 0), (0, 0, 0), (1, 0, 0)]
    assert np.linalg.norm(o.end_um - o.start_um, axis=1).sum() == pytest.approx(210.0, rel=1e-15)


def test_diagonal_segment_through_a_corner() -> None:
    s = seg((0.0, 0.0, 0.5), (100.0, 100.0, 0.5))
    out, table = assign_fields([s], [0.5], GRID)
    o = out[0]
    assert o.n == 2  # crosses x = 50 and y = 50 at the same point
    assert [tuple(table[f]["index"]) for f in o.field] == [(0, 0, 0), (1, 1, 0)]


def test_cylinder_in_fields() -> None:
    body = Cylinder(120.0, 2.0)
    p = WriteParameters(slicing_um=0.5, hatching_um=2.0, power_mW=10.0, speed_um_per_s=1e4)
    plain = slice_shell(body.shell(), p, resist="IP-S")
    split = slice_shell(body.shell(), p, resist="IP-S", fields=GRID)
    job = split.jobs[0]
    assert hatched_volume_um3(job, p) == pytest.approx(
        hatched_volume_um3(plain.jobs[0], p), rel=1e-12
    )
    # 3 × 3 fields touched by a circle of radius 120 µm, two height blocks of 1 µm
    assert len(job.fields) == 18
    assert job.field_size_um == [100.0, 100.0, 1.0]
    for ly in job.layers:
        s = ly.segments
        lo = np.array([GRID.bounds_of(job.fields[f]["index"])[0] for f in s.field])
        hi = np.array([GRID.bounds_of(job.fields[f]["index"])[1] for f in s.field])
        for pts in (s.start_um, s.end_um):
            assert np.all(pts >= lo - 1e-9) and np.all(pts <= hi + 1e-9)


def test_field_order_blocks_then_rows_serpentine() -> None:
    body = Cylinder(120.0, 2.0)
    p = WriteParameters(slicing_um=0.5, hatching_um=4.0, power_mW=10.0, speed_um_per_s=1e4)
    fields = slice_shell(body.shell(), p, resist="IP-S", fields=GRID).jobs[0].fields
    order = [tuple(f["index"]) for f in fields]
    first_block = [(i, j) for i, j, k in order[:9]]
    assert first_block == [
        (-1, -1),
        (0, -1),
        (1, -1),
        (1, 0),
        (0, 0),
        (-1, 0),
        (-1, 1),
        (0, 1),
        (1, 1),
    ]
    assert all(k == 0 for *_, k in order[:9]) and all(k == 1 for *_, k in order[9:])


def test_without_grid_one_field() -> None:
    p = WriteParameters(slicing_um=0.5, hatching_um=1.0, power_mW=10.0, speed_um_per_s=1e4)
    job = slice_shell(Cylinder(5.0, 1.0).shell(), p, resist="IP-S").jobs[0]
    assert job.fields == [{"index": [0, 0, 0], "center_um": [0.0, 0.0, 0.0]}]
    assert job.field_size_um is None
    assert all(np.all(ly.segments.field == 0) for ly in job.layers)


def test_invalid_grid() -> None:
    with pytest.raises(ValueError):
        FieldGrid(size_xy_um=0.0)
    assert math.isinf(FieldGrid(size_xy_um=10.0).size_z_um)
