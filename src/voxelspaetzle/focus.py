"""Focus kernels for the dose (spezifikation §3.2, §3.6; decision D8).

A kernel gives the normalised focal distribution g(x, y, z) in 1/µm² (∫ g dA = 1 in the focal
plane, |E|² sense). Until Raytatouille v1 provides the vector focus (D8), the Gaussian kernel of
§3.6 stands in; it is the only implementation here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Protocol

import numpy as np
from numpy.typing import NDArray


class FocusKernel(Protocol):
    def g(self, x: NDArray[Any], y: NDArray[Any], z: NDArray[Any]) -> NDArray[np.float64]: ...

    def extent_um(self) -> tuple[float, float, float]: ...

    def describe(self) -> dict[str, Any]: ...


@dataclass(frozen=True)
class GaussFocus:
    """g = (2/(π w₀²)) exp(−2ρ²/w₀²) exp(−2z²/w_z²); w₀, w_z are 1/e² half-axes in µm."""

    w0_um: float
    wz_um: float

    def __post_init__(self) -> None:
        if not (self.w0_um > 0.0 and self.wz_um > 0.0):
            raise ValueError("w0_um and wz_um must be positive")

    def g(self, x: NDArray[Any], y: NDArray[Any], z: NDArray[Any]) -> NDArray[np.float64]:
        rho2 = np.asarray(x, dtype=float) ** 2 + np.asarray(y, dtype=float) ** 2
        z2 = np.asarray(z, dtype=float) ** 2
        out: NDArray[np.float64] = (2.0 / (math.pi * self.w0_um**2)) * np.exp(
            -2.0 * rho2 / self.w0_um**2 - 2.0 * z2 / self.wz_um**2
        )
        return out

    def extent_um(self) -> tuple[float, float, float]:
        """Half-extent of g² kept in the convolution: 4 half-axes (rest below e⁻⁶⁴)."""
        return (4.0 * self.w0_um, 4.0 * self.w0_um, 4.0 * self.wz_um)

    def g2_factors(
        self, x: NDArray[Any], y: NDArray[Any], z: NDArray[Any]
    ) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
        """1D factors with g² = fx(x)·fy(y)·fz(z) (separable kernel, faster convolution)."""
        c = (2.0 / (math.pi * self.w0_um**2)) ** 2
        fx = c * np.exp(-4.0 * np.asarray(x, dtype=float) ** 2 / self.w0_um**2)
        fy = np.exp(-4.0 * np.asarray(y, dtype=float) ** 2 / self.w0_um**2)
        fz = np.exp(-4.0 * np.asarray(z, dtype=float) ** 2 / self.wz_um**2)
        return fx, fy, fz

    def describe(self) -> dict[str, Any]:
        return {"kind": "gauss", "w0_um": self.w0_um, "wz_um": self.wz_um}
