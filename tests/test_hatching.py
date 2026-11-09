"""Hatching of polygon loops (spezifikation §3.1, §3.9) against analytic chord lengths."""

from __future__ import annotations

import math

import numpy as np
import pytest
from numpy.typing import NDArray

from voxelspaetzle.hatching import hatch_loops, polygon_area, polygon_perimeter


def square(side: float, angle: float = 0.0) -> NDArray[np.float64]:
    pts = np.array([[0, 0], [side, 0], [side, side], [0, side]], dtype=float) - side / 2
    c, s = math.cos(angle), math.sin(angle)
    rot: NDArray[np.float64] = pts @ np.array([[c, s], [-s, c]])
    return rot


def circle(r: float, n: int, clockwise: bool = False) -> NDArray[np.float64]:
    t = np.linspace(0.0, 2 * math.pi, n, endpoint=False)
    pts = np.column_stack([r * np.cos(t), r * np.sin(t)])
    out: NDArray[np.float64] = pts[::-1] if clockwise else pts
    return out


def lengths(seg: NDArray[np.float64]) -> NDArray[np.float64]:
    out: NDArray[np.float64] = np.linalg.norm(seg[:, 1] - seg[:, 0], axis=1)
    return out


def test_square_axis_aligned() -> None:
    seg = hatch_loops([square(10.0)], spacing_um=1.0, angle_rad=0.0)
    assert seg.shape == (10, 2, 2)
    np.testing.assert_allclose(lengths(seg), 10.0, rtol=0, atol=1e-12)
    np.testing.assert_allclose(np.sort(seg[:, 0, 1]), np.arange(-4.5, 5.0, 1.0), atol=1e-12)


def test_rotated_square_hatched_along_its_edges() -> None:
    a = math.radians(30.0)
    seg = hatch_loops([square(10.0, a)], spacing_um=1.0, angle_rad=a)
    assert seg.shape[0] == 10
    np.testing.assert_allclose(lengths(seg), 10.0, atol=1e-9)
    d = (seg[:, 1] - seg[:, 0]) / lengths(seg)[:, None]
    np.testing.assert_allclose(np.abs(d @ np.array([math.cos(a), math.sin(a)])), 1.0, atol=1e-12)


def test_circle_chords() -> None:
    r, h = 10.0, 0.5
    seg = hatch_loops([circle(r, 200000)], spacing_um=h, angle_rad=0.0)
    c = seg[:, 0, 1]
    expected = 2 * np.sqrt(r * r - c * c)
    np.testing.assert_allclose(lengths(seg), expected, rtol=0, atol=1e-6)


def test_ring_has_two_segments_per_line_through_the_hole() -> None:
    loops = [circle(10.0, 20000), circle(4.0, 20000, clockwise=True)]
    seg = hatch_loops(loops, spacing_um=1.0, angle_rad=0.0)
    on_axis = seg[np.isclose(seg[:, 0, 1], 0.5)]
    assert on_axis.shape[0] == 2
    expected = math.sqrt(100 - 0.25) - math.sqrt(16 - 0.25)
    np.testing.assert_allclose(lengths(on_axis), expected, atol=1e-5)


def test_area_from_hatching_converges() -> None:
    loop = circle(10.0, 100000)
    errors = []
    for h in (1.0, 0.25, 0.0625):
        seg = hatch_loops([loop], spacing_um=h)
        errors.append(abs(lengths(seg).sum() * h - math.pi * 100) / (math.pi * 100))
    assert errors[0] < 1e-2
    assert errors[2] < errors[1] < errors[0]


def test_lines_through_vertices_and_along_edges() -> None:
    diamond = square(10.0, math.radians(45.0))  # vertices on the axes
    seg = hatch_loops([diamond], spacing_um=1.0, angle_rad=0.0, phase_um=0.0)
    assert np.all(lengths(seg) > 1e-9)
    through_vertex = seg[np.isclose(seg[:, 0, 1], 0.0)]
    np.testing.assert_allclose(lengths(through_vertex), 10.0 * math.sqrt(2.0), atol=1e-9)
    seg2 = hatch_loops([square(10.0)], spacing_um=1.0, angle_rad=0.0, phase_um=0.0)
    assert np.all(lengths(seg2) > 1e-9)  # lines on the bottom and top edge give no zero segments


def test_serpentine_alternates_direction() -> None:
    seg = hatch_loops([square(10.0)], spacing_um=1.0, serpentine=True)
    dx = np.sign(seg[:, 1, 0] - seg[:, 0, 0])
    assert np.all(dx[::2] == dx[0]) and np.all(dx[1::2] == -dx[0])
    uni = hatch_loops([square(10.0)], spacing_um=1.0, serpentine=False)
    assert np.all(uni[:, 1, 0] > uni[:, 0, 0])


def test_area_and_perimeter() -> None:
    assert polygon_area(square(2.0)) == pytest.approx(4.0)
    assert polygon_area(circle(1.0, 4, clockwise=True)) == pytest.approx(-2.0)
    assert polygon_perimeter(square(2.0)) == pytest.approx(8.0)


def test_invalid_spacing() -> None:
    with pytest.raises(ValueError):
        hatch_loops([square(1.0)], spacing_um=0.0)
