"""Exposure dose on a volume grid (spezifikation §3.4, §3.5, §5.3).

D(r) = k_p Σ P_f² ∫ g(r − r_f)² dt along the path: sample points with ds ≤ min(step, w)/4 carry
the weight P_f² ds / v (points: P_f² Δt), are spread trilinearly onto the grid nodes, and the
result is convolved with g² sampled on the grid (FFT). The source grid is padded by the kernel
extent, so path parts outside the output grid still contribute. Without a calibrated threshold
k_p = 1 and the dose is stored absolute in mW²·s/µm⁴.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.signal import fftconvolve

import voxelspaetzle
from voxelspaetzle import envelope
from voxelspaetzle.focus import FocusKernel
from voxelspaetzle.path import KIND_POINT, WritePath

FORMAT = "voxelspaetzle-field"
DOSE = "dose_mW2s_per_um4"


@dataclass(frozen=True)
class Grid:
    """Regular grid: lower corner ``origin_um`` and ``step_um`` in (x, y, z), ``shape`` (z, y, x).

    Values live at the cell centres origin + (index + ½)·step.
    """

    origin_um: tuple[float, float, float]
    step_um: tuple[float, float, float]
    shape: tuple[int, int, int]

    def __post_init__(self) -> None:
        if min(self.step_um) <= 0.0 or min(self.shape) < 1:
            raise ValueError("grid steps must be positive and the shape at least 1")


@dataclass
class VolumeField:
    grid: Grid
    data: dict[str, NDArray[Any]]
    focus: dict[str, Any] = field(default_factory=dict)
    source: dict[str, Any] = field(default_factory=dict)

    def save(self, path: str | Path) -> None:
        envelope.dump(
            path,
            FORMAT,
            {
                "origin_um": list(self.grid.origin_um),
                "step_um": list(self.grid.step_um),
                "shape": list(self.grid.shape),
                "fields": self.data,
                "focus": self.focus,
                "source": self.source,
            },
        )

    @classmethod
    def load(cls, path: str | Path) -> VolumeField:
        d = envelope.load(path, FORMAT)
        o, s, n = d["origin_um"], d["step_um"], d["shape"]
        grid = Grid((o[0], o[1], o[2]), (s[0], s[1], s[2]), (int(n[0]), int(n[1]), int(n[2])))
        return cls(grid, dict(d["fields"]), d["focus"], d["source"])


def _samples(path: WritePath, ds_max: float) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Sample points (N, 3) in µm and weights P² ds/v resp. P² Δt (mW²·s)."""
    pts, wts = [np.zeros((0, 3))], [np.zeros(0)]
    for job in path.jobs:
        for layer in job.layers:
            s = layer.segments
            point = s.kind == KIND_POINT
            if point.any():
                pts.append(s.start_um[point])
                wts.append(s.power_mW[point] ** 2 * s.dwell_s[point])
            m = ~point
            a, b = s.start_um[m], s.end_um[m]
            length = np.linalg.norm(b - a, axis=1)
            n = np.maximum(1, np.ceil(length / ds_max).astype(np.int64))
            seg = np.repeat(np.arange(a.shape[0]), n)
            k = np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n)
            t = (k + 0.5) / n[seg]  # midpoint rule on each segment
            pts.append(a[seg] + t[:, None] * (b - a)[seg])
            w = s.power_mW[m] ** 2 * length / (n * s.speed_um_per_s[m])
            wts.append(w[seg])
    return np.concatenate(pts), np.concatenate(wts)


def dose_field(
    path: WritePath,
    grid: Grid,
    focus: FocusKernel,
    power_factor: float = 1.0,
    k_p: float = 1.0,
) -> VolumeField:
    """Dose of ``path`` on ``grid`` (§3.4); ``power_factor`` = P_f/P from §3.3 (constant here)."""
    h = np.asarray(grid.step_um, dtype=float)
    ext = np.asarray(focus.extent_um(), dtype=float)
    pad = np.ceil(ext / h).astype(int)  # (x, y, z)
    ds = float(min(h.min(), min(ext) / 4.0) / 4.0)  # ext = 4 half-axes
    pts, w = _samples(path, ds)
    w = w * (power_factor**2) * k_p
    nz, ny, nx = grid.shape
    shape = (nz + 2 * pad[2], ny + 2 * pad[1], nx + 2 * pad[0])
    src = np.zeros(shape)
    if pts.size:
        # continuous index in the padded grid (x, y, z), cell centres at integers
        c = (pts - np.asarray(grid.origin_um)) / h - 0.5 + pad
        i0 = np.floor(c).astype(np.int64)
        f = c - i0
        lim = np.array([shape[2], shape[1], shape[0]])
        for dx in (0, 1):
            for dy in (0, 1):
                for dz in (0, 1):
                    idx = i0 + np.array([dx, dy, dz])
                    wt = w * np.where(dx, f[:, 0], 1 - f[:, 0])
                    wt = wt * np.where(dy, f[:, 1], 1 - f[:, 1])
                    wt = wt * np.where(dz, f[:, 2], 1 - f[:, 2])
                    ok = np.all((idx >= 0) & (idx < lim), axis=1)
                    np.add.at(src, (idx[ok, 2], idx[ok, 1], idx[ok, 0]), wt[ok])
    kx, ky, kz = (np.arange(-p, p + 1) * hk for p, hk in zip(pad, h, strict=True))
    factors = getattr(focus, "g2_factors", None)
    if factors is not None:  # separable kernel: three 1D convolutions
        fx, fy, fz = factors(kx, ky, kz)
        full = fftconvolve(src, fx[None, None, :], mode="same", axes=2)
        full = fftconvolve(full, fy[None, :, None], mode="same", axes=1)
        full = fftconvolve(full, fz[:, None, None], mode="same", axes=0)
    else:
        kernel = focus.g(kx[None, None, :], ky[None, :, None], kz[:, None, None]) ** 2
        full = fftconvolve(src, kernel, mode="same")
    dose = full[pad[2] : pad[2] + nz, pad[1] : pad[1] + ny, pad[0] : pad[0] + nx]
    source = {
        "program": "voxelspaetzle",
        "version": voxelspaetzle.__version__,
        "process": path.process,
        "power_factor": power_factor,
        "k_p": k_p,
        "sample_step_um": ds,
    }
    return VolumeField(grid, {DOSE: np.ascontiguousarray(dose)}, focus.describe(), source)
