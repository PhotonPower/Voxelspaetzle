"""Tolerance analysis over the process scatter (spezifikation §3.13, Testfall P28).

Perturbations act on a copy of the write path, in the order given:

- ``PowerNoise``: laser power × (1 + σ·ξ), ξ ~ N(0, 1), clipped at 0; one factor per segment,
  per layer or per job (``scope``).
- ``JobOffset``: alignment error between writing jobs; job 0 is the reference, every later job is
  shifted rigidly by an offset with standard deviations (σx, σy, σz).
- ``FieldOffset``: positioning error of the stage; all segments of one writing field are shifted
  by the same (δx, δy), independently per field (and per job).

``monte_carlo`` draws ``n`` perturbed paths from one seeded generator and evaluates a metric on
each; the draws are reproducible from the seed.
"""

from __future__ import annotations

import copy
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray

from voxelspaetzle.path import WritePath

SCOPES = ("segment", "layer", "job")


@dataclass(frozen=True)
class PowerNoise:
    rel_sigma: float
    scope: str = "segment"

    def __post_init__(self) -> None:
        if self.rel_sigma < 0.0:
            raise ValueError("rel_sigma must not be negative")
        if self.scope not in SCOPES:
            raise ValueError(f"scope must be one of {SCOPES}")


@dataclass(frozen=True)
class JobOffset:
    sigma_um: tuple[float, float, float]

    def __post_init__(self) -> None:
        if min(self.sigma_um) < 0.0:
            raise ValueError("sigma_um must not be negative")


@dataclass(frozen=True)
class FieldOffset:
    sigma_um: tuple[float, float]

    def __post_init__(self) -> None:
        if min(self.sigma_um) < 0.0:
            raise ValueError("sigma_um must not be negative")


Perturbation = PowerNoise | JobOffset | FieldOffset


@dataclass
class Draw:
    """A perturbed path and the drawn values (for provenance and evaluation)."""

    path: WritePath
    values: dict[str, Any] = field(default_factory=dict)


def _power(path: WritePath, p: PowerNoise, rng: np.random.Generator) -> list[Any]:
    drawn: list[Any] = []
    for job in path.jobs:
        job_factor = 1.0 + p.rel_sigma * rng.standard_normal() if p.scope == "job" else None
        per_job = []
        for layer in job.layers:
            s = layer.segments
            if p.scope == "segment":
                f = 1.0 + p.rel_sigma * rng.standard_normal(s.n)
            elif p.scope == "layer":
                f = np.full(s.n, 1.0 + p.rel_sigma * rng.standard_normal())
            else:
                f = np.full(s.n, job_factor)
            f = np.maximum(f, 0.0)
            s.power_mW = s.power_mW * f
            per_job.append(f)
        drawn.append(per_job)
    return drawn


def _job_offset(path: WritePath, p: JobOffset, rng: np.random.Generator) -> NDArray[np.float64]:
    off = np.zeros((len(path.jobs), 3))
    for j, job in enumerate(path.jobs):
        if j == 0:
            continue
        off[j] = np.asarray(p.sigma_um) * rng.standard_normal(3)
        for layer in job.layers:
            layer.segments.start_um = layer.segments.start_um + off[j]
            layer.segments.end_um = layer.segments.end_um + off[j]
    return off


def _field_offset(path: WritePath, p: FieldOffset, rng: np.random.Generator) -> list[Any]:
    drawn = []
    for job in path.jobs:
        off = np.asarray(p.sigma_um) * rng.standard_normal((len(job.fields), 2))
        for layer in job.layers:
            s = layer.segments
            shift = np.zeros((s.n, 3))
            shift[:, :2] = off[s.field]
            s.start_um = s.start_um + shift
            s.end_um = s.end_um + shift
        drawn.append(off)
    return drawn


def perturb(
    path: WritePath, perturbations: Sequence[Perturbation], rng: np.random.Generator
) -> Draw:
    """Copy of ``path`` with the perturbations applied in order."""
    out = copy.deepcopy(path)
    values: dict[str, Any] = {}
    for p in perturbations:
        if isinstance(p, PowerNoise):
            values[f"power_factor_{p.scope}"] = _power(out, p, rng)
        elif isinstance(p, JobOffset):
            values["job_offset_um"] = _job_offset(out, p, rng)
        else:
            values["field_offset_um"] = _field_offset(out, p, rng)
    return Draw(out, values)


@dataclass
class MonteCarlo:
    samples: NDArray[np.float64]
    seed: int
    perturbations: list[Perturbation]

    @property
    def mean(self) -> float:
        return float(np.mean(self.samples))

    @property
    def std(self) -> float:
        """Sample standard deviation (ddof = 1)."""
        return float(np.std(self.samples, ddof=1))


def monte_carlo(
    path: WritePath,
    perturbations: Sequence[Perturbation],
    metric: Callable[[WritePath], float],
    n: int,
    seed: int,
) -> MonteCarlo:
    """Metric over ``n`` perturbed paths drawn from ``numpy.random.default_rng(seed)``."""
    if n < 2:
        raise ValueError("n must be at least 2")
    rng = np.random.default_rng(seed)
    samples = np.array([metric(perturb(path, perturbations, rng).path) for _ in range(n)])
    return MonteCarlo(samples, seed, list(perturbations))
