"""Degree of polymerisation and the optical volume field (spezifikation §3.7).

V4a provides the interface and the limiting case without diffusion and with instant reaction
(threshold model, P6). Reaction–diffusion models (V4b) plug in as further models.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from voxelspaetzle.dose import DOSE, VolumeField
from voxelspaetzle.materials import Material


@dataclass(frozen=True)
class ThresholdModel:
    """α = 1 where D ≥ D_th, else 0 (no diffusion, instant reaction; §3.6, §3.7)."""

    d_th: float

    def alpha(self, dose: Any) -> Any:
        return (np.asarray(dose) >= self.d_th).astype(np.float64)

    def describe(self) -> dict[str, Any]:
        return {"kind": "threshold", "threshold_dose_mW2s_per_um4": self.d_th}


def degree_of_polymerization(f: VolumeField, model: ThresholdModel) -> VolumeField:
    """Field ``alpha`` ∈ [0, 1] from the dose field."""
    alpha = model.alpha(f.data[DOSE])
    return VolumeField(
        f.grid, {"alpha": alpha, "model": model.describe()}, dict(f.focus), dict(f.source)
    )


def optical_field(
    alpha_field: VolumeField,
    material: Material,
    wavelengths_um: Sequence[float],
    developed: bool = True,
    surrounding: tuple[str, float] = ("air", 1.0),
    alpha_dev: float = 0.5,
    missing_kappa: str = "error",
) -> VolumeField:
    """Fields ``n`` and ``kappa`` of shape (nλ, z, y, x) for the printed part (§5.3).

    ``developed``: resist with α < ``alpha_dev`` is washed away and replaced by the surrounding
    medium (name, real index, κ = 0); otherwise the whole volume is resist with n(λ, α), κ(λ, α).
    Absorption the material data do not give is an error; with ``missing_kappa = "nan"`` the
    resist gets κ = NaN at those wavelengths, listed in ``kappa_missing_um``.
    """
    if missing_kappa not in ("error", "nan"):
        raise ValueError('missing_kappa must be "error" or "nan"')
    a = np.asarray(alpha_field.data["alpha"], dtype=float)
    solid = a >= alpha_dev if developed else np.ones(a.shape, dtype=bool)
    n = np.empty((len(wavelengths_um), *a.shape))
    k = np.empty_like(n)
    missing: list[float] = []
    for i, lam in enumerate(wavelengths_um):
        n[i] = np.where(solid, material.n(lam, a), surrounding[1] if developed else 0.0)
        try:
            k[i] = np.where(solid, material.kappa(lam, a), 0.0)
        except ValueError:
            if missing_kappa == "error":
                raise
            k[i] = np.where(solid, np.nan, 0.0)
            missing.append(float(lam))
    labels = (a >= alpha_dev).astype(np.uint8)
    names = [surrounding[0] if developed else f"{material.name} liquid", material.name]
    data: dict[str, Any] = {
        "n": n,
        "kappa": k,
        "wavelengths_um": [float(x) for x in wavelengths_um],
        "material": labels,
        "materials": names,
        "alpha_dev": alpha_dev,
        "kappa_missing_um": missing,
    }
    return VolumeField(alpha_field.grid, data, dict(alpha_field.focus), dict(alpha_field.source))
