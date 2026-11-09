"""Write path data model and file format ``voxelspaetzle-path`` (spezifikation §3.1, §5.2)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from voxelspaetzle import envelope

FORMAT = "voxelspaetzle-path"
KIND_CONTOUR = 0
KIND_HATCH = 1
KIND_POINT = 2


@dataclass
class Segments:
    """Segments of one layer; arrays of length N (positions (N, 3) in µm, printer frame)."""

    start_um: NDArray[np.float64]
    end_um: NDArray[np.float64]
    power_mW: NDArray[np.float64]
    speed_um_per_s: NDArray[np.float64]
    kind: NDArray[np.int8]
    dwell_s: NDArray[np.float64]
    region: NDArray[np.int32]

    def __post_init__(self) -> None:
        self.start_um = np.asarray(self.start_um, dtype=np.float64).reshape(-1, 3)
        self.end_um = np.asarray(self.end_um, dtype=np.float64).reshape(-1, 3)
        n = self.start_um.shape[0]
        self.power_mW = np.asarray(self.power_mW, dtype=np.float64).reshape(n)
        self.speed_um_per_s = np.asarray(self.speed_um_per_s, dtype=np.float64).reshape(n)
        self.kind = np.asarray(self.kind, dtype=np.int8).reshape(n)
        self.dwell_s = np.asarray(self.dwell_s, dtype=np.float64).reshape(n)
        self.region = np.asarray(self.region, dtype=np.int32).reshape(n)
        if self.end_um.shape != (n, 3):
            raise ValueError("start_um and end_um must have the same shape (N, 3)")
        moving = self.kind != KIND_POINT
        if np.any(self.speed_um_per_s[moving] <= 0.0):
            raise ValueError("speed_um_per_s must be positive for contour and hatch segments")
        if np.any(self.power_mW < 0.0) or np.any(self.dwell_s < 0.0):
            raise ValueError("power_mW and dwell_s must not be negative")

    @property
    def n(self) -> int:
        return int(self.start_um.shape[0])

    @classmethod
    def concatenate(cls, parts: list[Segments]) -> Segments:
        if not parts:
            z = np.zeros(0)
            return cls(
                np.zeros((0, 3)),
                np.zeros((0, 3)),
                z,
                z,
                z.astype(np.int8),
                z,
                z.astype(np.int32),
            )
        return cls(*(np.concatenate([getattr(p, f) for p in parts]) for f in _SEG_FIELDS))

    def to_dict(self) -> dict[str, Any]:
        return {f: getattr(self, f) for f in _SEG_FIELDS}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Segments:
        return cls(*(d[f] for f in _SEG_FIELDS))


_SEG_FIELDS = (
    "start_um",
    "end_um",
    "power_mW",
    "speed_um_per_s",
    "kind",
    "dwell_s",
    "region",
)


@dataclass
class Layer:
    z_um: float
    hatch_angle_rad: float
    segments: Segments


@dataclass
class Job:
    """One writing job in one resist; ``markers`` are alignment marks for the next job."""

    resist: str
    layers: list[Layer] = field(default_factory=list)
    markers: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class WritePath:
    """Complete write path (§5.2): jobs in print order, pose printer → part, provenance."""

    process: str
    jobs: list[Job] = field(default_factory=list)
    pose: NDArray[np.float64] = field(default_factory=lambda: np.eye(4))
    postprocess: list[dict[str, Any]] = field(default_factory=list)
    source: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "process": self.process,
            "pose": np.asarray(self.pose, dtype=np.float64),
            "jobs": [
                {
                    "resist": j.resist,
                    "markers": j.markers,
                    "layers": [
                        {
                            "z_um": ly.z_um,
                            "hatch_angle_rad": ly.hatch_angle_rad,
                            "segments": ly.segments.to_dict(),
                        }
                        for ly in j.layers
                    ],
                }
                for j in self.jobs
            ],
            "postprocess": self.postprocess,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> WritePath:
        jobs = [
            Job(
                resist=j["resist"],
                markers=j["markers"],
                layers=[
                    Layer(
                        float(ly["z_um"]),
                        float(ly["hatch_angle_rad"]),
                        Segments.from_dict(ly["segments"]),
                    )
                    for ly in j["layers"]
                ],
            )
            for j in d["jobs"]
        ]
        return cls(d["process"], jobs, np.asarray(d["pose"]), d["postprocess"], d["source"])

    def save(self, path: str | Path, npz_threshold: int = 1_000_000) -> None:
        envelope.dump(path, FORMAT, self.to_dict(), npz_threshold)

    @classmethod
    def load(cls, path: str | Path) -> WritePath:
        return cls.from_dict(envelope.load(path, FORMAT))
