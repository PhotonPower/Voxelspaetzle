"""Slicer: closed body → write path with contours and hatching (spezifikation §3.1, §3.9)."""

from __future__ import annotations

import hashlib
import math
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import nurbforge as nf
from numpy.typing import NDArray

import voxelspaetzle
from voxelspaetzle.fields import FieldGrid, assign_fields
from voxelspaetzle.geometry import body_z_range, section_loops, slice_heights
from voxelspaetzle.hatching import hatch_loops, inside_loops
from voxelspaetzle.offset import offset_loops
from voxelspaetzle.path import KIND_CONTOUR, KIND_HATCH, Job, Layer, Segments, WritePath


@dataclass(frozen=True)
class WriteParameters:
    """Writing parameters of one parameter set (µm, mW, µm/s, rad).

    ``hatch_angle_rad`` is the angle of layer 0, ``hatch_angle_step_rad`` is added per layer
    (π/2 alternates the direction, schmid2023). Contours (§3.9): ``contour_count`` loops per
    section loop, the first at ``contour_offset_um`` into the solid (typically half the line
    width), the next ones ``contour_spacing_um`` further in (default: ``hatching_um``). The
    hatching fills the section moved in by ``hatch_offset_um``.
    """

    slicing_um: float
    hatching_um: float
    power_mW: float
    speed_um_per_s: float
    hatch_angle_rad: float = 0.0
    hatch_angle_step_rad: float = math.pi / 2
    contour_count: int = 1
    contour_offset_um: float = 0.0
    contour_spacing_um: float | None = None
    hatch_offset_um: float = 0.0
    serpentine: bool = True
    chord_tol_um: float = 1e-3

    def __post_init__(self) -> None:
        for name in ("slicing_um", "hatching_um", "speed_um_per_s", "chord_tol_um"):
            if not getattr(self, name) > 0.0:
                raise ValueError(f"{name} must be positive")
        if self.power_mW < 0.0:
            raise ValueError("power_mW must not be negative")
        if self.contour_count < 0:
            raise ValueError("contour_count must not be negative")
        if self.contour_offset_um < 0.0 or self.hatch_offset_um < 0.0:
            raise ValueError("offsets must not be negative")
        if self.contour_spacing_um is not None and not self.contour_spacing_um > 0.0:
            raise ValueError("contour_spacing_um must be positive")


def _segments(xy: NDArray[np.float64], z: float, kind: int, p: WriteParameters) -> Segments:
    n = xy.shape[0]
    zz = np.full((n, 1), z)
    return Segments(
        start_um=np.hstack([xy[:, 0], zz]),
        end_um=np.hstack([xy[:, 1], zz]),
        power_mW=np.full(n, p.power_mW),
        speed_um_per_s=np.full(n, p.speed_um_per_s),
        kind=np.full(n, kind, dtype=np.int8),
        dwell_s=np.zeros(n),
        region=np.zeros(n, dtype=np.int32),
        field=np.zeros(n, dtype=np.int32),
    )


def input_hash(shell: Any) -> str:
    """SHA-256 of the body as STEP text with fixed name and timestamp (provenance, §5)."""
    text = nf.to_step(shell, name="body", timestamp="2000-01-01T00:00:00")
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()


def slice_shell(
    shell: Any,
    params: WriteParameters,
    resist: str,
    process: str = "",
    z_range_um: tuple[float, float] | None = None,
    fields: FieldGrid | None = None,
    exclude: Sequence[Any] = (),
) -> WritePath:
    """Write path of one job for a closed shell (µm, part frame = printer frame).

    ``fields`` splits the path into writing fields (§3.10). ``exclude`` are bodies written by
    earlier jobs (§3.11, overlap rule ``priority``): their sections are removed from the
    hatching on the same grid, and contour pieces inside them are dropped.
    """
    z_min, z_max, critical = body_z_range(shell)
    if z_range_um is not None:
        z_min, z_max = z_range_um
    for other in exclude:
        critical += body_z_range(other)[2]
    heights = slice_heights(z_min, z_max, params.slicing_um, critical)
    parts_per_layer: list[Segments] = []
    angles: list[float] = []
    for k, z in enumerate(heights):
        loops = section_loops(shell, float(z), params.chord_tol_um)
        cut = [
            lp for other in exclude for lp in section_loops(other, float(z), params.chord_tol_um)
        ]
        angle = (params.hatch_angle_rad + k * params.hatch_angle_step_rad) % math.pi
        parts = []
        spacing = params.contour_spacing_um or params.hatching_um
        for c in range(params.contour_count):
            for lp in offset_loops(loops, params.contour_offset_um + c * spacing):
                edges = np.stack([lp, np.roll(lp, -1, axis=0)], 1)
                if cut:
                    edges = edges[~inside_loops(edges.mean(axis=1), cut)]
                parts.append(_segments(edges, z, KIND_CONTOUR, params))
        hatch = hatch_loops(
            offset_loops(loops, params.hatch_offset_um),
            params.hatching_um,
            angle,
            serpentine=params.serpentine,
            exclude=cut,
        )
        parts.append(_segments(hatch, z, KIND_HATCH, params))
        parts_per_layer.append(Segments.concatenate(parts))
        angles.append(float(angle))
    split, table = assign_fields(parts_per_layer, [float(z) for z in heights], fields)
    layers = [Layer(float(z), a, sg) for z, a, sg in zip(heights, angles, split, strict=True)]
    size = None if fields is None else [fields.size_xy_um, fields.size_xy_um, fields.size_z_um]
    source = {
        "slicer": "voxelspaetzle",
        "version": voxelspaetzle.__version__,
        "parameters": asdict(params),
        "input_sha256": input_hash(shell),
    }
    job = Job(resist=resist, layers=layers, fields=table, field_size_um=size)
    return WritePath(process=process, jobs=[job], source=source)


def hatched_volume_um3(job: Job, params: WriteParameters) -> float:
    """Volume covered by the hatching: Σ segment length × hatching × slicing (µm³, P1)."""
    total = 0.0
    for ly in job.layers:
        s = ly.segments
        m = s.kind == KIND_HATCH
        total += float(np.linalg.norm(s.end_um[m] - s.start_um[m], axis=1).sum())
    return total * params.hatching_um * params.slicing_um
