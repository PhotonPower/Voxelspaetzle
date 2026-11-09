"""Inward offsets of section loops (spezifikation §3.9): exact miter offsets and cleanup."""

from __future__ import annotations

import math

import numpy as np
import pytest
from numpy.typing import NDArray

from voxelspaetzle.hatching import polygon_area, polygon_perimeter
from voxelspaetzle.offset import offset_loops


def poly(*pts: tuple[float, float]) -> NDArray[np.float64]:
    return np.array(pts, dtype=float)


def circle(r: float, n: int = 20000, clockwise: bool = False) -> NDArray[np.float64]:
    t = np.linspace(0.0, 2 * math.pi, n, endpoint=False)
    out: NDArray[np.float64] = np.column_stack([r * np.cos(t), r * np.sin(t)])
    return out[::-1].copy() if clockwise else out


SQUARE = poly((0, 0), (10, 0), (10, 10), (0, 10))
L_SHAPE = poly((0, 0), (10, 0), (10, 4), (4, 4), (4, 10), (0, 10))


def test_zero_offset_is_identity() -> None:
    (out,) = offset_loops([SQUARE], 0.0)
    np.testing.assert_array_equal(out, SQUARE)


def test_square() -> None:
    (out,) = offset_loops([SQUARE], 1.0)
    assert polygon_area(out) == pytest.approx(64.0, abs=1e-12)
    assert polygon_perimeter(out) == pytest.approx(32.0, abs=1e-12)


def test_concave_corner_is_mitered() -> None:
    (out,) = offset_loops([L_SHAPE], 1.0)
    assert polygon_area(out) == pytest.approx(28.0, abs=1e-12)
    assert any(np.allclose(p, (3.0, 3.0)) for p in out)


def test_circle_and_ring() -> None:
    (out,) = offset_loops([circle(10.0)], 1.0)
    assert polygon_area(out) == pytest.approx(math.pi * 81, rel=1e-6)
    assert polygon_perimeter(out) == pytest.approx(2 * math.pi * 9, rel=1e-6)
    outer, hole = offset_loops([circle(10.0), circle(4.0, clockwise=True)], 1.0)
    assert polygon_area(outer) == pytest.approx(math.pi * 81, rel=1e-6)
    assert polygon_area(hole) == pytest.approx(-math.pi * 25, rel=1e-6)


def test_small_island_vanishes() -> None:
    out = offset_loops([circle(10.0), poly((20, 0), (20.5, 0), (20.5, 0.5), (20, 0.5))], 1.0)
    assert len(out) == 1
    assert polygon_area(out[0]) == pytest.approx(math.pi * 81, rel=1e-6)


def test_thin_tooth_vanishes() -> None:
    tooth = poly((0, 0), (10, 0), (10, 10), (5.25, 10), (5.25, 13), (4.75, 13), (4.75, 10), (0, 10))
    (out,) = offset_loops([tooth], 1.0)
    assert polygon_area(out) == pytest.approx(64.0, abs=1e-9)
    assert out[:, 1].max() == pytest.approx(9.0, abs=1e-12)


def test_wide_tooth_is_kept() -> None:
    tooth = poly((0, 0), (10, 0), (10, 10), (7, 10), (7, 13), (3, 13), (3, 10), (0, 10))
    (out,) = offset_loops([tooth], 1.0)
    assert polygon_area(out) == pytest.approx(64.0 + 2 * 3, abs=1e-9)


def test_slot_widens() -> None:
    slot = poly((0, 0), (10, 0), (10, 10), (5.25, 10), (5.25, 7), (4.75, 7), (4.75, 10), (0, 10))
    (out,) = offset_loops([slot], 1.0)
    # square 8 × 8 minus the widened slot 2.5 × 3 (from y = 6 to y = 9)
    assert polygon_area(out) == pytest.approx(64.0 - 2.5 * 3, abs=1e-9)


def test_wall_thinner_than_twice_the_offset_vanishes() -> None:
    out = offset_loops([circle(5.0), circle(4.5, clockwise=True)], 0.5)
    assert out == []


def test_touching_offsets_raise() -> None:
    # two islands 1 µm apart side by side growing holes would be fine; a C-shape whose arms
    # come within 2δ after offsetting is not resolved by the local cleanup
    c_shape = poly((0, 0), (10, 0), (10, 4), (2, 4), (2, 6), (10, 6), (10, 10), (0, 10))
    with pytest.raises(ValueError, match="intersect"):
        offset_loops([c_shape], 1.5)
