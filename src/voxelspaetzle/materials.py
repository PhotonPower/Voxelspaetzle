"""Material data ``voxelspaetzle-material`` (D7, spezifikation §3.7, §5.6).

Refractive index of the cured state as a dispersion formula, the liquid state as an offset,
absorption as α (1/mm, read in) at given wavelengths and returned as κ = αλ/(4π). Values between
liquid (α = 0) and cured (α = 1) are interpolated linearly in the degree of polymerisation α.
Wavelengths outside the measured range and absorption at wavelengths the sources do not give are
refused, not extrapolated.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import ArrayLike, NDArray

from voxelspaetzle import envelope

FORMAT = "voxelspaetzle-material"
_SAME_WAVELENGTH_UM = 1e-9


@dataclass
class Material:
    name: str
    index: dict[str, Any]
    liquid_offset: dict[str, Any]
    absorption: list[dict[str, Any]] = field(default_factory=list)
    interpolation: str = "linear_in_alpha"
    sources: list[str] = field(default_factory=list)
    notes: str = ""

    def __post_init__(self) -> None:
        if self.index.get("model") != "sellmeier" or self.index.get("state") != "cured":
            raise ValueError("only a Sellmeier formula of the cured state is supported")
        if self.interpolation != "linear_in_alpha":
            raise ValueError("only linear interpolation in alpha is supported")

    def _cured(self, lam: float) -> float:
        lo, hi = self.index["range_um"]
        if not lo <= lam <= hi:
            raise ValueError(f"{self.name}: {lam} µm outside the measured range {lo}…{hi} µm")
        l2 = lam * lam
        terms = zip(self.index["B"], self.index["C_um2"], strict=True)
        return math.sqrt(1.0 + sum(b * l2 / (l2 - c) for b, c in terms))

    def n(self, wavelength_um: float, alpha: ArrayLike) -> Any:
        """Real refractive index at the vacuum wavelength for degree of polymerisation α."""
        cured = self._cured(wavelength_um)
        liquid = cured - float(self.liquid_offset["delta_n"])
        a = np.asarray(alpha, dtype=float)
        out = liquid + a * (cured - liquid)
        return float(out) if out.ndim == 0 else out

    def kappa(self, wavelength_um: float, alpha: ArrayLike) -> Any:
        """Extinction coefficient κ = αλ/(4π) from the absorption given at this wavelength."""
        for entry in self.absorption:
            if abs(entry["wavelength_um"] - wavelength_um) <= _SAME_WAVELENGTH_UM:
                k = entry["alpha_per_mm"] * wavelength_um * 1e-3 / (4.0 * math.pi)
                a = np.asarray(alpha, dtype=float)
                out: NDArray[np.float64] = np.full(a.shape, k)
                return float(out) if out.ndim == 0 else out
        raise ValueError(f"{self.name}: absorption at {wavelength_um} µm not given in the sources")

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}

    def save(self, path: str | Path) -> None:
        envelope.dump(path, FORMAT, self.to_dict())


def list_materials() -> list[str]:
    d = resources.files("voxelspaetzle") / "materials"
    return sorted(p.name.removesuffix(".json") for p in d.iterdir() if p.name.endswith(".json"))


def load_material(name_or_path: str | Path) -> Material:
    """A shipped material by name, or a material file."""
    if isinstance(name_or_path, str):
        f = resources.files("voxelspaetzle") / "materials" / f"{name_or_path}.json"
        if f.is_file():
            return Material(**envelope.load(Path(str(f)), FORMAT))
    return Material(**envelope.load(Path(name_or_path), FORMAT))
