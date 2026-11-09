"""Slicer: closed body → write path with contours and hatching (spezifikation §3.1, §3.9)."""

from __future__ import annotations

import hashlib
import math
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import nurbforge as nf
from numpy.typing import NDArray

import voxelspaetzle
from voxelspaetzle.geometry import body_z_range, section_loops, slice_heights
from voxelspaetzle.hatching import hatch_loops
from voxelspaetzle.path import KIND_CONTOUR, KIND_HATCH, Job, Layer, Segments, WritePath


@dataclass(frozen=True)
class WriteParameters:
    """Writing parameters of one parameter set (µm, mW, µm/s, rad).

    ``hatch_angle_rad`` is the angle of layer 0, ``hatch_angle_step_rad`` is added per layer
    (π/2 alternates the direction, schmid2023). ``contour`` writes each section loop once at
    offset 0 before the hatching (inward offsets follow in V1c).
    """

    slicing_um: float
    hatching_um: float
    power_mW: float
    speed_um_per_s: float
    hatch_angle_rad: float = 0.0
    hatch_angle_step_rad: float = math.pi / 2
    contour: bool = True
    serpentine: bool = True
    chord_tol_um: float = 1e-3

    def __post_init__(self) -> None:
        for name in ("slicing_um", "hatching_um", "speed_um_per_s", "chord_tol_um"):
            if not getattr(self, name) > 0.0:
                raise ValueError(f"{name} must be positive")
        if self.power_mW < 0.0:
            raise ValueError("power_mW must not be negative")


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
) -> WritePath:
    """Write path of one job for a closed shell (µm, part frame = printer frame)."""
    z_min, z_max, critical = body_z_range(shell)
    if z_range_um is not None:
        z_min, z_max = z_range_um
    layers = []
    for k, z in enumerate(slice_heights(z_min, z_max, params.slicing_um, critical)):
        loops = section_loops(shell, float(z), params.chord_tol_um)
        angle = (params.hatch_angle_rad + k * params.hatch_angle_step_rad) % math.pi
        parts = []
        if params.contour:
            for lp in loops:
                parts.append(
                    _segments(np.stack([lp, np.roll(lp, -1, axis=0)], 1), z, KIND_CONTOUR, params)
                )
        hatch = hatch_loops(loops, params.hatching_um, angle, serpentine=params.serpentine)
        parts.append(_segments(hatch, z, KIND_HATCH, params))
        layers.append(Layer(float(z), float(angle), Segments.concatenate(parts)))
    source = {
        "slicer": "voxelspaetzle",
        "version": voxelspaetzle.__version__,
        "parameters": asdict(params),
        "input_sha256": input_hash(shell),
    }
    return WritePath(process=process, jobs=[Job(resist=resist, layers=layers)], source=source)


def hatched_volume_um3(job: Job, params: WriteParameters) -> float:
    """Volume covered by the hatching: Σ segment length × hatching × slicing (µm³, P1)."""
    total = 0.0
    for ly in job.layers:
        s = ly.segments
        m = s.kind == KIND_HATCH
        total += float(np.linalg.norm(s.end_um[m] - s.start_um[m], axis=1).sum())
    return total * params.hatching_um * params.slicing_um
