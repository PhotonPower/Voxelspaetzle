"""Process library ``voxelspaetzle-process`` (spezifikation §5.1) with the reference processes."""

from __future__ import annotations

import math
import re
from pathlib import Path

import pytest

from voxelspaetzle.assembly import BodySpec
from voxelspaetzle.process import Process, list_processes, load_process

DOCS = Path(__file__).resolve().parents[1] / "docs"


def test_reference_processes_are_shipped() -> None:
    assert {"schmid2023-A", "toulouse2021-B"} <= set(list_processes())


def test_process_a_values_from_schmid2023() -> None:
    p = load_process("schmid2023-A")
    assert p.printer["wavelength_um"] == 0.78
    assert p.printer["power_100pct_mW"] == 58.0
    assert p.objective["na"] == 0.8 and p.objective["working_distance_um"] == 380.0
    assert p.mode == "dip_in_wrapped"
    ap = p.write_parameters("IP-Black", "aperture")
    assert (ap.slicing_um, ap.hatching_um, ap.power_mW, ap.speed_um_per_s) == (2.0, 1.0, 58.0, 4e4)
    lens = p.write_parameters("IP-S", "lens")
    assert lens.power_mW == pytest.approx(0.7 * 58.0)
    assert lens.speed_um_per_s == 5e4
    assert lens.hatch_angle_step_rad == pytest.approx(math.pi / 2)


def test_process_b_values_from_toulouse2021() -> None:
    p = load_process("toulouse2021-B")
    s = p.write_parameters("IP-Dip", "spectrometer")
    assert (s.slicing_um, s.hatching_um, s.power_mW, s.speed_um_per_s) == (0.1, 0.25, 7.5, 1.5e4)
    assert s.hatch_angle_rad == pytest.approx(math.pi / 2) and s.hatch_angle_step_rad == 0.0
    assert p.objective["na"] is None  # not stated in the paper
    assert [d["medium"] for d in p.development] == ["PGMEA", "isopropanol", "nitrogen blower"]


def test_unknown_values_are_not_invented() -> None:
    p = load_process("schmid2023-A")
    with pytest.raises(ValueError, match="not given"):
        p.write_parameters("IP-Black", "lens")
    with pytest.raises(KeyError):
        p.write_parameters("IP-Q", "lens")


def test_sources_are_in_the_source_list() -> None:
    known = set(re.findall(r"^\| (\w+) \|", (DOCS / "quellen.md").read_text(), re.M))
    for name in list_processes():
        assert set(load_process(name).sources) <= known


def test_roundtrip_and_body_spec(tmp_path: Path) -> None:
    p = load_process("toulouse2021-B")
    f = tmp_path / "custom.process.json"
    p.save(f)
    q = load_process(f)
    assert q == p
    spec = BodySpec.from_process("Hull", p, "IP-Dip", "spectrometer")
    assert spec.material == "IP-Dip" and spec.params == p.write_parameters("IP-Dip", "spectrometer")
    assert isinstance(q, Process)
