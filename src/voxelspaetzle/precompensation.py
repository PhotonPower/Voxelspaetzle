"""Pre-compensation: proximity correction of the dose and inverse problems (spezifikation §3.14).

``segment_kernel`` gives the dose at points per P² of every segment in closed form for the
Gaussian kernel (horizontal segments: error functions along the segment). ``proximity_correction``
sets the power of every segment so that the dose at all segment midpoints (points: their position)
equals a target: a linear problem in q = P², solved with non-negative least squares.
``solve_parameter`` finds a parameter (power, scale factor, …) for which a simulated quantity hits
its target (Illinois variant of regula falsi); ``scale_path`` scales a path about a point, e.g. the
axial pre-compensation of shrinkage (fischer2013: factor 1.28 in z).
"""

from __future__ import annotations

import copy
import math
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import nnls
from scipy.special import erf

from voxelspaetzle.focus import GaussFocus
from voxelspaetzle.path import KIND_POINT, Segments, WritePath

FloatArray = NDArray[np.float64]


def _all_segments(path: WritePath) -> Segments:
    return Segments.concatenate([ly.segments for job in path.jobs for ly in job.layers])


def segment_kernel(
    points_um: FloatArray, path: WritePath, focus: GaussFocus, k_p: float = 1.0
) -> FloatArray:
    """Dose at ``points_um`` (M, 3) per P² (mW²) of each segment (M, N), Gaussian kernel (§3.6).

    Moving segments must be horizontal (constant z), as written by the slicer.
    """
    s = _all_segments(path)
    p = np.asarray(points_um, dtype=float).reshape(-1, 3)
    w0, wz = focus.w0_um, focus.wz_um
    c = (2.0 / (math.pi * w0**2)) ** 2
    a, b = s.start_um, s.end_um
    out = np.zeros((p.shape[0], s.n))
    point = s.kind == KIND_POINT
    if point.any():
        r = p[:, None, :] - a[None, point, :]
        rho2 = r[..., 0] ** 2 + r[..., 1] ** 2
        out[:, point] = (
            c * np.exp(-4 * rho2 / w0**2 - 4 * r[..., 2] ** 2 / wz**2) * s.dwell_s[point]
        )
    m = ~point
    if m.any():
        if np.any(np.abs(b[m, 2] - a[m, 2]) > 1e-12):
            raise NotImplementedError("closed form only for horizontal segments")
        d = b[m, :2] - a[m, :2]
        length = np.linalg.norm(d, axis=1)
        e = d / length[:, None]
        r = p[:, None, :2] - a[None, m, :2]
        t = np.einsum("mnk,nk->mn", r, e)
        perp2 = np.einsum("mnk,mnk->mn", r, r) - t**2
        dz = p[:, None, 2] - a[None, m, 2]
        along = (math.sqrt(math.pi) * w0 / 4) * (erf(2 * t / w0) - erf(2 * (t - length) / w0))
        out[:, m] = (
            c
            * np.exp(-4 * np.maximum(perp2, 0.0) / w0**2 - 4 * dz**2 / wz**2)
            * along
            / s.speed_um_per_s[m]
        )
    return out * k_p


def proximity_correction(
    path: WritePath, focus: GaussFocus, target_dose: float, k_p: float = 1.0
) -> WritePath:
    """Copy of ``path`` with powers that give ``target_dose`` at all segment midpoints."""
    s = _all_segments(path)
    mids = np.where((s.kind == KIND_POINT)[:, None], s.start_um, 0.5 * (s.start_um + s.end_um))
    k = segment_kernel(mids, path, focus, k_p)
    q, residual = nnls(k, np.full(s.n, float(target_dose)))
    power = np.sqrt(q)
    out = copy.deepcopy(path)
    i = 0
    for job in out.jobs:
        for layer in job.layers:
            n = layer.segments.n
            layer.segments.power_mW = power[i : i + n].copy()
            i += n
    out.source = {
        **path.source,
        "proximity_correction": {
            "target_dose_mW2s_per_um4": float(target_dose),
            "focus": focus.describe(),
            "k_p": k_p,
            "relative_residual": float(residual / (math.sqrt(s.n) * target_dose)),
        },
    }
    return out


def scale_path(
    path: WritePath,
    factors: tuple[float, float, float],
    centre_um: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> WritePath:
    """Copy of ``path`` with r' = c + f·(r − c) (also layer heights and stage positions)."""
    f = np.asarray(factors, dtype=float)
    if np.any(f <= 0.0):
        raise ValueError("scale factors must be positive")
    c = np.asarray(centre_um, dtype=float)
    out = copy.deepcopy(path)
    for job in out.jobs:
        for layer in job.layers:
            s = layer.segments
            s.start_um = c + f * (s.start_um - c)
            s.end_um = c + f * (s.end_um - c)
            layer.z_um = float(c[2] + f[2] * (layer.z_um - c[2]))
        for fd in job.fields:
            fd["center_um"] = [float(v) for v in c + f * (np.asarray(fd["center_um"]) - c)]
    out.source = {**path.source, "scaled": {"factors": f.tolist(), "centre_um": c.tolist()}}
    return out


@dataclass
class Solution:
    x: float
    value: float
    converged: bool
    history: list[tuple[float, float]] = field(default_factory=list)


def solve_parameter(
    simulate: Callable[[float], float],
    target: float,
    x0: float,
    x1: float,
    tol: float = 1e-6,
    max_iter: int = 40,
) -> Solution:
    """Parameter x in [x0, x1] with simulate(x) = target (Illinois method; needs a bracket)."""
    f0, f1 = simulate(x0) - target, simulate(x1) - target
    history: list[tuple[float, float]] = [(x0, f0 + target), (x1, f1 + target)]
    if f0 * f1 > 0:
        raise ValueError("target not bracketed by simulate(x0) and simulate(x1)")
    side = 0
    x, fx = x1, f1
    for _ in range(max_iter):
        x = (x0 * f1 - x1 * f0) / (f1 - f0)
        fx = simulate(x) - target
        history.append((x, fx + target))
        if abs(fx) <= tol:
            return Solution(x, fx + target, True, history)
        if fx * f1 > 0:
            x1, f1 = x, fx
            if side == -1:
                f0 /= 2
            side = -1
        else:
            x0, f0 = x, fx
            if side == 1:
                f1 /= 2
            side = 1
    return Solution(x, fx + target, False, history)
