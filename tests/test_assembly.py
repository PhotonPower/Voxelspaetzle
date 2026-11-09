"""Writing jobs and multi-material printing (spezifikation §3.11)."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import nurbforge as nf
import pytest
from bodies import Cylinder, Ring

from voxelspaetzle.assembly import BodySpec, read_step_bodies, slice_assembly
from voxelspaetzle.path import WritePath
from voxelspaetzle.slicer import WriteParameters, hatched_volume_um3

P = WriteParameters(slicing_um=0.5, hatching_um=0.25, power_mW=20.0, speed_um_per_s=1e4)


def write_step(tmp_path: Path, bodies: dict[str, object]) -> Path:
    f = tmp_path / "part.step"
    nf.write_step(str(f), list(bodies.values()), unit="um", names=list(bodies))
    return f


def test_read_named_bodies(tmp_path: Path) -> None:
    f = write_step(
        tmp_path, {"Lens": Cylinder(10.0, 5.0).shell(), "Aperture": Ring(20, 12, 5).shell()}
    )
    bodies = read_step_bodies(f)
    assert list(bodies) == ["Lens", "Aperture"]
    assert abs(bodies["Lens"].volume()) == pytest.approx(math.pi * 500, rel=1e-9)


def test_two_jobs_in_order(tmp_path: Path) -> None:
    f = write_step(
        tmp_path, {"Lens": Cylinder(10.0, 5.0).shell(), "Aperture": Ring(20, 12, 5).shell()}
    )
    specs = [
        BodySpec("Lens", "IP-S", P),
        BodySpec("Aperture", "IP-Black", P, markers=[{"type": "cross", "center_um": [30, 0, 0]}]),
    ]
    path = slice_assembly(read_step_bodies(f), specs, process="schmid2023-A")
    assert [j.resist for j in path.jobs] == ["IP-S", "IP-Black"]
    assert path.jobs[1].markers == [{"type": "cross", "center_um": [30, 0, 0]}]
    assert hatched_volume_um3(path.jobs[0], P) == pytest.approx(math.pi * 100 * 5, rel=5e-3)
    assert hatched_volume_um3(path.jobs[1], P) == pytest.approx(math.pi * (400 - 144) * 5, rel=5e-3)
    assert path.source["bodies"] == ["Lens", "Aperture"]


def test_fill_body_becomes_postprocess() -> None:
    bodies = {"Hull": Ring(20, 12, 5).shell(), "Ink": Cylinder(11.0, 5.0).shell()}
    specs = [BodySpec("Hull", "IP-Dip", P), BodySpec("Ink", "NPS-J", None, kind="fill")]
    path = slice_assembly(bodies, specs, process="toulouse2021-B")
    assert [j.resist for j in path.jobs] == ["IP-Dip"]
    assert path.postprocess == [
        {"type": "fill", "material": "NPS-J", "body": "Ink", "after_job": 0}
    ]


def test_overlap_is_an_error_by_default() -> None:
    bodies = {"Lens": Cylinder(14.0, 5.0).shell(), "Aperture": Ring(20, 12, 5).shell()}
    specs = [BodySpec("Lens", "IP-S", P), BodySpec("Aperture", "IP-Black", P)]
    with pytest.raises(ValueError, match="overlap"):
        slice_assembly(bodies, specs, process="x")


def test_overlap_priority_earlier_body_wins() -> None:
    bodies = {"Lens": Cylinder(14.0, 5.0).shell(), "Aperture": Ring(20, 12, 5).shell()}
    specs = [BodySpec("Lens", "IP-S", P), BodySpec("Aperture", "IP-Black", P)]
    path = slice_assembly(bodies, specs, process="x", overlap="priority")
    assert hatched_volume_um3(path.jobs[0], P) == pytest.approx(math.pi * 196 * 5, rel=5e-3)
    assert hatched_volume_um3(path.jobs[1], P) == pytest.approx(math.pi * (400 - 196) * 5, rel=5e-3)
    # no hatch point of the aperture lies inside the lens
    for ly in path.jobs[1].layers:
        s = ly.segments
        mid = 0.5 * (s.start_um + s.end_um)
        assert np.all(np.hypot(mid[:, 0], mid[:, 1]) > 14.0 - 1e-3)


def test_unknown_body_or_kind() -> None:
    bodies = {"Lens": Cylinder(5.0, 1.0).shell()}
    with pytest.raises(ValueError, match="Missing"):
        slice_assembly(bodies, [BodySpec("Missing", "IP-S", P)], process="x")
    with pytest.raises(ValueError):
        BodySpec("Lens", "IP-S", None)  # write needs parameters


def test_assembly_roundtrip(tmp_path: Path) -> None:
    from voxelspaetzle.fields import FieldGrid

    bodies = {"Lens": Cylinder(10.0, 1.0).shell()}
    path = slice_assembly(
        bodies, [BodySpec("Lens", "IP-S", P)], process="x", fields=FieldGrid(size_xy_um=8.0)
    )
    f = tmp_path / "a.json"
    path.save(f)
    back = WritePath.load(f)
    assert back.jobs[0].fields == path.jobs[0].fields
    assert back.jobs[0].field_size_um == path.jobs[0].field_size_um
    a, b = path.jobs[0].layers[0].segments, back.jobs[0].layers[0].segments
    assert a.field.tobytes() == b.field.tobytes()


def test_overlap_volume_on_the_writing_grid() -> None:
    from voxelspaetzle.assembly import overlap_volume_um3

    lens, ap = Cylinder(14.0, 5.0).shell(), Ring(20, 12, 5).shell()
    v = overlap_volume_um3(lens, ap, slicing_um=0.25, hatching_um=0.1)
    assert v == pytest.approx(math.pi * (196 - 144) * 5, rel=5e-3)
    assert overlap_volume_um3(Cylinder(10.0, 5.0).shell(), ap, 0.25, 0.1) == 0.0
    touching = Ring(20, 14, 5).shell()  # inner wall on the lens wall
    assert overlap_volume_um3(lens, touching, 0.25, 0.1) < 1e-6
