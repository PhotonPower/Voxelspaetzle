"""P1: write path against the CAD body (spezifikation §3.1, §3.9; docs/testfaelle.md)."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import nurbforge as nf
import pytest
from bodies import Cylinder, Ring, SphericalCap

from voxelspaetzle.geometry import section_loops, slice_heights
from voxelspaetzle.hatching import polygon_area, polygon_perimeter
from voxelspaetzle.path import KIND_CONTOUR, KIND_HATCH, WritePath
from voxelspaetzle.slicer import WriteParameters, hatched_volume_um3, slice_shell

PARAMS = WriteParameters(slicing_um=0.5, hatching_um=0.25, power_mW=20.0, speed_um_per_s=1e4)


def test_layer_heights_midpoint_rule() -> None:
    z = slice_heights(0.0, 5.0, 0.5)
    np.testing.assert_allclose(z, np.arange(0.25, 5.0, 0.5), atol=1e-12)
    np.testing.assert_allclose(np.diff(z), 0.5, atol=1e-12)


def test_layer_heights_avoid_critical_heights() -> None:
    z = slice_heights(0.0, 2.0, 0.5, critical=[0.75], eps_um=1e-6)
    assert np.all(np.abs(z - 0.75) >= 1e-6 * 0.999)
    assert len(z) == 4


@pytest.mark.parametrize("body", [Cylinder(10.0, 5.0), SphericalCap(50.0, 10.0)])
def test_sections_match_analytic_circles(body: Cylinder | SphericalCap) -> None:
    shell = body.shell()
    for z in (0.3, 2.5, 4.9):
        loops = section_loops(shell, z, chord_tol_um=1e-4)
        assert len(loops) == 1
        r = body.radius_at(z)
        assert polygon_area(loops[0]) == pytest.approx(math.pi * r * r, rel=1e-4)
        assert polygon_perimeter(loops[0]) == pytest.approx(2 * math.pi * r, rel=1e-4)


def test_ring_section_has_outer_and_hole() -> None:
    loops = section_loops(Ring(10.0, 4.0, 5.0).shell(), 2.5, chord_tol_um=1e-4)
    areas = sorted(polygon_area(lp) for lp in loops)
    assert areas == pytest.approx([-math.pi * 16, math.pi * 100], rel=1e-4)


def test_cylinder_path() -> None:
    body = Cylinder(10.0, 5.0)
    path = slice_shell(body.shell(), PARAMS, resist="IP-S", process="test")
    layers = path.jobs[0].layers
    assert len(layers) == 10
    np.testing.assert_allclose(np.diff([ly.z_um for ly in layers]), 0.5, atol=1e-12)
    for k, ly in enumerate(layers):
        assert ly.hatch_angle_rad == pytest.approx((k * math.pi / 2) % math.pi)
        seg = ly.segments
        assert np.all(seg.start_um[:, 2] == ly.z_um) and np.all(seg.end_um[:, 2] == ly.z_um)
        assert set(np.unique(seg.kind)) == {KIND_CONTOUR, KIND_HATCH}
        assert np.all(seg.power_mW == 20.0) and np.all(seg.speed_um_per_s == 1e4)
    v = hatched_volume_um3(path.jobs[0], PARAMS)
    assert v == pytest.approx(body.volume(), rel=5e-3)


def test_cap_volume_converges() -> None:
    body = SphericalCap(50.0, 10.0)
    shell = body.shell()
    errors = []
    for d in (0.5, 0.2, 0.1):
        p = WriteParameters(slicing_um=d, hatching_um=d, power_mW=20.0, speed_um_per_s=1e4)
        v = hatched_volume_um3(slice_shell(shell, p, resist="IP-S").jobs[0], p)
        errors.append(abs(v - body.volume()) / body.volume())
    assert errors[2] < errors[1] < errors[0]
    assert errors[2] < 2e-3


def test_hatch_midpoints_lie_inside_the_body() -> None:
    body = Ring(10.0, 4.0, 5.0)
    shell = body.shell()
    path = slice_shell(shell, PARAMS, resist="IP-S")
    rng = np.random.default_rng(7)
    for ly in path.jobs[0].layers[::3]:
        seg = ly.segments
        idx = np.flatnonzero(seg.kind == KIND_HATCH)
        for i in rng.choice(idx, size=min(20, idx.size), replace=False):
            mid = 0.5 * (seg.start_um[i] + seg.end_um[i])
            assert nf.point_in_shell(shell, tuple(float(x) for x in mid))
    assert hatched_volume_um3(path.jobs[0], PARAMS) == pytest.approx(body.volume(), rel=1e-2)


def test_path_roundtrip(tmp_path: Path) -> None:
    path = slice_shell(Cylinder(5.0, 1.0).shell(), PARAMS, resist="IP-S", process="test")
    f = tmp_path / "path.json"
    path.save(f)
    back = WritePath.load(f)
    assert back.process == "test" and back.jobs[0].resist == "IP-S"
    a, b = path.jobs[0].layers[0].segments, back.jobs[0].layers[0].segments
    assert a.start_um.tobytes() == b.start_um.tobytes()
    assert a.kind.tobytes() == b.kind.tobytes()
    assert back.source["parameters"]["slicing_um"] == 0.5
    assert len(back.source["input_sha256"]) == 64


def test_contours_with_offsets() -> None:
    body = Cylinder(10.0, 2.0)
    p = WriteParameters(
        slicing_um=0.5,
        hatching_um=0.1,
        power_mW=20.0,
        speed_um_per_s=1e4,
        contour_count=2,
        contour_offset_um=0.25,
        contour_spacing_um=0.5,
        hatch_offset_um=0.75,
        chord_tol_um=1e-4,
    )
    job = slice_shell(body.shell(), p, resist="IP-S").jobs[0]
    for ly in job.layers:
        s = ly.segments
        c = s.kind == KIND_CONTOUR
        r = np.hypot(s.start_um[c, 0], s.start_um[c, 1])
        np.testing.assert_allclose(np.sort(np.unique(np.round(r, 3))), [9.25, 9.75], atol=1e-3)
        h = s.kind == KIND_HATCH
        assert np.hypot(s.start_um[h, 0], s.start_um[h, 1]).max() <= 9.25 + 1e-6
    assert hatched_volume_um3(job, p) == pytest.approx(math.pi * 9.25**2 * 2.0, rel=2e-3)


def test_contour_parameters_are_checked() -> None:
    with pytest.raises(ValueError):
        WriteParameters(slicing_um=1, hatching_um=1, power_mW=1, speed_um_per_s=1, contour_count=-1)
    with pytest.raises(ValueError):
        WriteParameters(
            slicing_um=1, hatching_um=1, power_mW=1, speed_um_per_s=1, contour_offset_um=-0.1
        )
