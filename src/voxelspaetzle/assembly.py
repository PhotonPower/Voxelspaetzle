"""Writing jobs and multi-material printing from named bodies (spezifikation §3.11)."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import nurbforge as nf

import voxelspaetzle
from voxelspaetzle.fields import FieldGrid
from voxelspaetzle.geometry import body_z_range, section_loops, slice_heights
from voxelspaetzle.hatching import common_length, line_intervals
from voxelspaetzle.path import WritePath
from voxelspaetzle.process import Process
from voxelspaetzle.slicer import WriteParameters, slice_shell

KINDS = ("write", "fill")
OVERLAP_RULES = ("error", "priority")


@dataclass(frozen=True)
class BodySpec:
    """Role of one named body: material, parameter set and kind.

    ``kind = "write"`` makes a writing job in resist ``material`` with ``params``;
    ``kind = "fill"`` is a post-processing step (e.g. ink ``NPS-J`` into a printed basin) after
    the last writing job listed before it. ``markers`` are passed through to the job.
    """

    name: str
    material: str
    params: WriteParameters | None
    kind: str = "write"
    markers: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_process(
        cls, name: str, process: Process, resist: str, parameter_set: str, **kw: Any
    ) -> BodySpec:
        """Writing body with resist and parameter set from a process (§5.1)."""
        return cls(name, resist, process.write_parameters(resist, parameter_set), **kw)

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"kind must be one of {KINDS}")
        if self.kind == "write" and self.params is None:
            raise ValueError(f"body {self.name!r}: a writing job needs parameters")


def read_step_bodies(path: str | Path) -> dict[str, Any]:
    """Named bodies of a STEP file in µm (Nurbforge ``read_step_named``), oriented."""
    out: dict[str, Any] = {}
    for name, shell in nf.read_step_named(str(path), unit="um"):
        if name in out:
            raise ValueError(f"body name {name!r} occurs twice in {path}")
        out[str(name)] = shell.oriented()
    return out


def overlap_volume_um3(a: Any, b: Any, slicing_um: float, hatching_um: float) -> float:
    """Volume common to two closed shells, measured on a writing grid (§3.11).

    Layers by the midpoint rule over the common height range, on each layer the length common to
    the inside intervals of both sections along hatch lines (angle 0, phase h/2), times h·Δz.
    Disjoint and touching bodies give 0. Same grid rule as the hatching, so the result is the
    volume that both jobs would write.
    """
    za0, za1, ca = body_z_range(a)
    zb0, zb1, cb = body_z_range(b)
    z0, z1 = max(za0, zb0), min(za1, zb1)
    if z1 <= z0:
        return 0.0
    total = 0.0
    for z in slice_heights(z0, z1, slicing_um, ca + cb):
        la, lb = section_loops(a, float(z)), section_loops(b, float(z))
        if la and lb:
            ia = line_intervals(la, hatching_um, 0.0, 0.5 * hatching_um)
            ib = line_intervals(lb, hatching_um, 0.0, 0.5 * hatching_um)
            total += common_length(*ia, *ib)
    return total * hatching_um * slicing_um


def slice_assembly(
    bodies: Mapping[str, Any],
    specs: Sequence[BodySpec],
    process: str,
    fields: FieldGrid | None = None,
    overlap: str = "error",
    overlap_tol_um3: float = 1e-9,
) -> WritePath:
    """Write path with one job per writing body, in the order of ``specs``.

    Overlapping writing bodies are an error (``overlap = "error"``) or the earlier body wins
    (``"priority"``): later jobs leave out the volume of all earlier writing bodies.
    """
    if overlap not in OVERLAP_RULES:
        raise ValueError(f"overlap must be one of {OVERLAP_RULES}")
    for sp in specs:
        if sp.name not in bodies:
            raise ValueError(f"body {sp.name!r} not in the input ({sorted(bodies)})")
    writers = [sp for sp in specs if sp.kind == "write"]
    if overlap == "error":
        for n, a in enumerate(writers):
            for b in writers[n + 1 :]:
                assert a.params is not None and b.params is not None
                v = overlap_volume_um3(
                    bodies[a.name],
                    bodies[b.name],
                    min(a.params.slicing_um, b.params.slicing_um),
                    min(a.params.hatching_um, b.params.hatching_um),
                )
                if v > overlap_tol_um3:
                    raise ValueError(f"bodies {a.name!r} and {b.name!r} overlap by {v:.6g} µm³")
    path = WritePath(process=process)
    earlier: list[Any] = []
    for sp in specs:
        if sp.kind == "fill":
            if not path.jobs:
                raise ValueError(f"fill body {sp.name!r} comes before any writing job")
            path.postprocess.append(
                {
                    "type": "fill",
                    "material": sp.material,
                    "body": sp.name,
                    "after_job": len(path.jobs) - 1,
                }
            )
            continue
        assert sp.params is not None
        exclude = earlier if overlap == "priority" else []
        job = slice_shell(
            bodies[sp.name], sp.params, sp.material, process, fields=fields, exclude=exclude
        ).jobs[0]
        job.markers = list(sp.markers)
        path.jobs.append(job)
        earlier.append(bodies[sp.name])
    names = [sp.name for sp in specs]
    text = nf.to_step([bodies[n] for n in names], names=names, timestamp="2000-01-01T00:00:00")
    path.source = {
        "slicer": "voxelspaetzle",
        "version": voxelspaetzle.__version__,
        "bodies": names,
        "specs": [
            {
                "name": sp.name,
                "material": sp.material,
                "kind": sp.kind,
                "parameters": None if sp.params is None else asdict(sp.params),
            }
            for sp in specs
        ],
        "overlap": overlap,
        "input_sha256": hashlib.sha256(str(text).encode("utf-8")).hexdigest(),
    }
    return path
