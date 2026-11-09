"""Outputs to the framework programs (spezifikation §3.12, §5.4).

- BWPM: label grid with one complex index per label, lengths in mm, as in ``bwpm.adapter.Structure``
  (BWPM is not a dependency; ``BwpmStructure.to_bwpm()`` converts if it is installed).
- FourierGrating: one period of the voxel solid as ``lamellar1d`` layers from bottom to top, the
  exact voxel staircase.
- STL: closed surface of the developed voxels (faces between solid and non-solid), in µm.
- Transmission along z through an optical field.
"""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from voxelspaetzle.dose import VolumeField

FloatArray = NDArray[np.float64]
_UM_TO_MM = 1e-3


def _wavelength_index(f: VolumeField, wavelength_um: float) -> int:
    for i, lam in enumerate(f.data["wavelengths_um"]):
        if abs(lam - wavelength_um) <= 1e-9:
            return i
    raise ValueError(f"wavelength {wavelength_um} µm not in the optical field")


@dataclass(frozen=True)
class BwpmStructure:
    """Fields of ``bwpm.adapter.Structure`` (lengths in mm) plus the quantisation error."""

    nx: int
    ny: int
    dx: float
    dy: float
    dz: float
    indices: tuple[complex, ...]
    labels: NDArray[np.int32]
    index_before: complex
    z0: float
    mask_width: float
    wavelength_um: float
    max_index_error: float

    def to_bwpm(self) -> Any:
        """``bwpm.adapter.Structure`` (needs the BWPM package)."""
        from bwpm.adapter import Structure  # type: ignore[import-not-found]

        return Structure(
            self.nx,
            self.ny,
            self.dx,
            self.dy,
            self.dz,
            self.indices,
            self.labels,
            self.index_before,
            self.z0,
            self.mask_width,
        )


def bwpm_structure(
    optical: VolumeField,
    wavelength_um: float,
    index_before: complex,
    max_levels: int = 16,
    mask_width_um: float = 0.0,
) -> BwpmStructure:
    """Label grid for BWPM at one wavelength (§3.12).

    If the field has at most ``max_levels`` distinct complex indices they are kept exactly;
    otherwise n is divided into ``max_levels`` equal bins (centre value, κ averaged per bin) and
    the largest deviation |ñ − ñ_level| is reported. Missing absorption (NaN) is an error.
    """
    i = _wavelength_index(optical, wavelength_um)
    n = np.asarray(optical.data["n"][i], dtype=float)
    k = np.asarray(optical.data["kappa"][i], dtype=float)
    if np.isnan(k).any() or np.isnan(n).any():
        raise ValueError("kappa (or n) missing in the optical field at this wavelength")
    v = n + 1j * k
    levels, inverse = np.unique(v.ravel(), return_inverse=True)
    if levels.size <= max_levels:
        labels = inverse.reshape(v.shape).astype(np.int32)
        indices = tuple(complex(x) for x in levels)
    else:
        lo, hi = float(n.min()), float(n.max())
        w = (hi - lo) / max_levels
        b = np.clip(np.floor((n - lo) / w).astype(int), 0, max_levels - 1)
        used, labels_flat = np.unique(b.ravel(), return_inverse=True)
        kk = np.bincount(labels_flat, weights=k.ravel()) / np.bincount(labels_flat)
        indices = tuple(complex(lo + (u + 0.5) * w, kk[j]) for j, u in enumerate(used))
        labels = labels_flat.reshape(v.shape).astype(np.int32)
    err = float(np.abs(v - np.asarray(indices)[labels]).max())
    g = optical.grid
    nz, ny, nx = g.shape
    return BwpmStructure(
        nx,
        ny,
        g.step_um[0] * _UM_TO_MM,
        g.step_um[1] * _UM_TO_MM,
        g.step_um[2] * _UM_TO_MM,
        indices,
        labels,
        complex(index_before),
        g.origin_um[2] * _UM_TO_MM,
        mask_width_um * _UM_TO_MM,
        float(wavelength_um),
        err,
    )


def fourier_grating_layers(
    alpha_field: VolumeField, y_index: int, solid: str, background: str, alpha_dev: float = 0.5
) -> tuple[float, list[dict[str, Any]]]:
    """Period (µm) and ``lamellar1d`` layers (bottom → top) of the row ``y_index`` (§3.12).

    The grid width in x is one period. Breakpoints lie on voxel boundaries, measured from the
    grid origin; consecutive identical voxel layers are merged.
    """
    a = np.asarray(alpha_field.data["alpha"], dtype=float)[:, y_index, :] >= alpha_dev
    hx, _, hz = alpha_field.grid.step_um
    nx = a.shape[1]
    period = nx * hx
    layers: list[dict[str, Any]] = []
    previous: tuple[bool, ...] | None = None
    for row in a:
        key = tuple(bool(x) for x in row)
        if key == previous:
            layers[-1]["thickness_um"] += hz
            continue
        change = [0, *[j for j in range(1, nx) if row[j] != row[j - 1]], nx]
        layers.append(
            {
                "type": "lamellar1d",
                "thickness_um": hz,
                "breakpoints_um": [j * hx for j in change],
                "materials": [solid if row[j] else background for j in change[:-1]],
            }
        )
        previous = key
    return period, layers


def surface_triangles(alpha_field: VolumeField, alpha_dev: float = 0.5) -> FloatArray:
    """Triangles (N, 3, 3) in µm on the faces between solid and non-solid voxels."""
    s = np.pad(np.asarray(alpha_field.data["alpha"], dtype=float) >= alpha_dev, 1).astype(np.int8)
    o = np.asarray(alpha_field.grid.origin_um)
    h = np.asarray(alpha_field.grid.step_um)
    tris = []
    for ax in range(3):  # axis in (x, y, z); array axis 2 − ax
        b, c = (ax + 1) % 3, (ax + 2) % 3
        d = np.diff(s, axis=2 - ax)
        for sign in (1, -1):  # +1: empty → solid along +ax, outward normal −ax
            idx = np.argwhere(d == sign)  # (k, j, i) in the diff array
            if idx.size == 0:
                continue
            pos = np.stack([idx[:, 2], idx[:, 1], idx[:, 0]], axis=1).astype(float)  # (x, y, z)
            pos[:, ax] += 1.0  # boundary between padded cells i and i + 1
            base = o + (pos - 1.0) * h  # padded index → voxel coordinates
            eb, ec = np.zeros(3), np.zeros(3)
            eb[b], ec[c] = h[b], h[c]
            p0, p1, p2, p3 = base, base + eb, base + eb + ec, base + ec
            if sign == 1:  # normal −ax: reverse the cyclic order
                tris += [np.stack([p0, p3, p2], 1), np.stack([p0, p2, p1], 1)]
            else:
                tris += [np.stack([p0, p1, p2], 1), np.stack([p0, p2, p3], 1)]
    return np.concatenate(tris) if tris else np.zeros((0, 3, 3))


def write_stl(alpha_field: VolumeField, path: str | Path, alpha_dev: float = 0.5) -> int:
    """Binary STL of the developed voxels (µm, float32 as the format requires); triangle count."""
    tri = surface_triangles(alpha_field, alpha_dev)
    with open(path, "wb") as fh:
        fh.write(b"voxelspaetzle voxel surface, micrometre".ljust(80, b" "))
        fh.write(struct.pack("<I", tri.shape[0]))
        for t in tri:
            nrm = np.cross(t[1] - t[0], t[2] - t[0])
            nrm = nrm / (np.linalg.norm(nrm) or 1.0)
            fh.write(struct.pack("<12fH", *nrm, *t[0], *t[1], *t[2], 0))
    return int(tri.shape[0])


def read_stl(path: str | Path) -> FloatArray:
    """Triangles (N, 3, 3) of a binary STL file."""
    data = Path(path).read_bytes()
    (count,) = struct.unpack_from("<I", data, 80)
    rec = np.frombuffer(
        data,
        dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]),
        count=count,
        offset=84,
    )
    return np.asarray(rec["v"], dtype=np.float64)


def transmission_along_z(optical: VolumeField, wavelength_um: float) -> FloatArray:
    """T(x, y) = exp(−Σ 4πκ Δz/λ) through the whole field along z (§3.3, P11)."""
    i = _wavelength_index(optical, wavelength_um)
    k = np.asarray(optical.data["kappa"][i], dtype=float)
    depth = 4.0 * math.pi * k.sum(axis=0) * optical.grid.step_um[2] / wavelength_um
    out: FloatArray = np.exp(-depth)
    return out
