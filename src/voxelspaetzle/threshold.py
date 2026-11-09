"""Threshold model and its measures (spezifikation §3.6, Testfälle P4, P5).

Solid is where the dose reaches D_th. Line widths, heights and surfaces are taken where the dose
crosses D_th, linearly interpolated between grid values; with the Gaussian kernel these follow
the closed forms of §3.6 (the tests use them as references).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from voxelspaetzle import envelope
from voxelspaetzle.dose import DOSE, VolumeField
from voxelspaetzle.focus import GaussFocus

HEIGHTMAP = "voxelspaetzle-heightmap"
MIN_WIDTH_FRACTION = 0.4  # of the dose FWHM (fischer2013, Abschn. 2)

FloatArray = NDArray[np.float64]


def _centres(f: VolumeField, axis: int) -> FloatArray:
    """Cell centres along x (0), y (1) or z (2) in µm."""
    n = f.grid.shape[2 - axis]
    out = f.grid.origin_um[axis] + (np.arange(n) + 0.5) * f.grid.step_um[axis]
    return np.asarray(out, dtype=np.float64)


def _edge(values: FloatArray, coords: FloatArray, level: float, start: int, step: int) -> float:
    """Coordinate where ``values`` falls below ``level`` walking from ``start`` by ``step``."""
    i = start
    while 0 <= i + step < values.size and values[i + step] >= level:
        i += step
    j = i + step
    if not 0 <= j < values.size:
        return math.nan  # the solid reaches the grid boundary
    t = (values[i] - level) / (values[i] - values[j])
    return float(coords[i] + t * (coords[j] - coords[i]))


def _extent(values: FloatArray, coords: FloatArray, level: float, peak: int) -> float:
    if values[peak] < level:
        return 0.0
    return _edge(values, coords, level, peak, 1) - _edge(values, coords, level, peak, -1)


@dataclass(frozen=True)
class LineSize:
    """Cross-section of a line along x: width (y), height (z), dose FWHM in y, all in µm.

    ``unreliable``: width below 40 % of the dose FWHM (§3.6). ``width_sensitivity`` is
    (Δd/d)/(ΔP/P) = 1/ln(D_peak/D_th) for a Gaussian profile (dose ∝ P²).
    """

    width_um: float
    height_um: float
    fwhm_um: float
    peak_dose: float
    unreliable: bool
    width_sensitivity: float


def gauss_line_size(focus: GaussFocus, d0: float, d_th: float) -> tuple[float, float]:
    """Width w₀√(ln(D₀/D_th)) and height w_z√(ln(D₀/D_th)) of a line or voxel (§3.6)."""
    if d0 <= d_th:
        return 0.0, 0.0
    r = math.sqrt(math.log(d0 / d_th))
    return focus.w0_um * r, focus.wz_um * r


def line_size(f: VolumeField, d_th: float, x_um: float) -> LineSize:
    """Cross-section of a line along x at the grid column nearest to ``x_um``."""
    d: FloatArray = f.data[DOSE]
    ix = int(np.argmin(np.abs(_centres(f, 0) - x_um)))
    plane = d[:, :, ix]  # (z, y)
    kz, ky = np.unravel_index(int(np.argmax(plane)), plane.shape)
    peak = float(plane[kz, ky])
    y, z = _centres(f, 1), _centres(f, 2)
    width = _extent(plane[kz, :], y, d_th, int(ky))
    height = _extent(plane[:, ky], z, d_th, int(kz))
    fwhm = _extent(plane[kz, :], y, 0.5 * peak, int(ky))
    sens = 1.0 / math.log(peak / d_th) if peak > d_th else math.inf
    return LineSize(width, height, fwhm, peak, width < MIN_WIDTH_FRACTION * fwhm, sens)


def solid_field(f: VolumeField, d_th: float, material: str) -> VolumeField:
    """Solid mask D ≥ D_th as material field (0 = developed away, 1 = ``material``; §5.3)."""
    mask = (f.data[DOSE] >= d_th).astype(np.uint8)
    data: dict[str, Any] = {
        "material": mask,
        "materials": ["none", material],
        "threshold_dose_mW2s_per_um4": float(d_th),
    }
    return VolumeField(f.grid, data, dict(f.focus), dict(f.source))


@dataclass
class HeightMap:
    """Height z(x, y) of the top surface on a regular grid (§5.5); NaN where nothing is solid."""

    origin_um: tuple[float, float]
    step_um: tuple[float, float]
    z_um: FloatArray  # (ny, nx)
    material_below: str
    material_above: str
    clipped: bool = False
    source: dict[str, Any] = field(default_factory=dict)

    def save(self, path: str | Path) -> None:
        envelope.dump(
            path,
            HEIGHTMAP,
            {
                "origin_um": list(self.origin_um),
                "step_um": list(self.step_um),
                "z_um": self.z_um,
                "material_below": self.material_below,
                "material_above": self.material_above,
                "clipped": self.clipped,
                "source": self.source,
            },
        )

    @classmethod
    def load(cls, path: str | Path) -> HeightMap:
        d = envelope.load(path, HEIGHTMAP)
        o, s = d["origin_um"], d["step_um"]
        return cls(
            (o[0], o[1]),
            (s[0], s[1]),
            d["z_um"],
            d["material_below"],
            d["material_above"],
            bool(d["clipped"]),
            d["source"],
        )


def height_map(
    f: VolumeField, d_th: float, material_below: str = "solid", material_above: str = "none"
) -> HeightMap:
    """Top surface: highest crossing of D_th in each column, interpolated in z (§3.6)."""
    d: FloatArray = f.data[DOSE]
    solid = d >= d_th
    nz = d.shape[0]
    any_solid = solid.any(axis=0)
    top = nz - 1 - np.argmax(solid[::-1], axis=0)  # highest solid index per column
    clipped = bool(np.any(any_solid & (top == nz - 1)))
    above = np.minimum(top + 1, nz - 1)
    d_top = np.take_along_axis(d, top[None], axis=0)[0]
    d_above = np.take_along_axis(d, above[None], axis=0)[0]
    with np.errstate(divide="ignore", invalid="ignore"):
        t = (d_top - d_th) / (d_top - d_above)
    z = _centres(f, 2)
    zz = z[top] + t * f.grid.step_um[2]
    zz = np.where(any_solid & (top < nz - 1), zz, np.nan)
    ox = f.grid.origin_um[0] + 0.5 * f.grid.step_um[0]
    oy = f.grid.origin_um[1] + 0.5 * f.grid.step_um[1]
    return HeightMap(
        (ox, oy),
        (f.grid.step_um[0], f.grid.step_um[1]),
        np.asarray(zz, dtype=np.float64),
        material_below,
        material_above,
        clipped,
        {"threshold_dose_mW2s_per_um4": float(d_th), **f.source},
    )


def wall_profile(f: VolumeField, d_th: float, x_um: float) -> FloatArray:
    """Position y(z) of the wall on the +y side at the column nearest ``x_um`` (NaN if none)."""
    d: FloatArray = f.data[DOSE]
    ix = int(np.argmin(np.abs(_centres(f, 0) - x_um)))
    y = _centres(f, 1)
    out = np.full(d.shape[0], np.nan)
    for k in range(d.shape[0]):
        row = d[k, :, ix]
        j = int(np.argmax(row))
        if row[j] >= d_th:
            out[k] = _edge(row, y, d_th, j, 1)
    return out


def spectrum(profile: FloatArray, step_um: float) -> tuple[FloatArray, FloatArray]:
    """One-sided amplitude spectrum: spatial frequencies (1/µm) and amplitudes (µm)."""
    p = np.asarray(profile, dtype=np.float64)
    n = p.size
    amp = np.abs(np.fft.rfft(p)) / n
    amp[1:] *= 2.0
    if n % 2 == 0:
        amp[-1] /= 2.0
    freq = np.asarray(np.fft.rfftfreq(n, step_um), dtype=np.float64)
    return freq, amp
