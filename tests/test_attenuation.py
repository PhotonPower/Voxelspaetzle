"""P12: attenuation of the writing beam in an absorbing resist (spezifikation §3.3)."""

from __future__ import annotations

import math

import pytest
from scipy.special import expn

from voxelspaetzle.attenuation import (
    alpha_per_mm_from_kappa,
    cone_transmission,
    focus_power_mW,
    kappa_from_alpha_per_mm,
)


def test_kappa_alpha_roundtrip() -> None:
    k = kappa_from_alpha_per_mm(1.0, 0.78)
    assert k == pytest.approx(1.0 * 0.78e-3 / (4 * math.pi), rel=1e-15)
    assert alpha_per_mm_from_kappa(k, 0.78) == pytest.approx(1.0, rel=1e-15)


def test_schmid2023_wrapped_objective() -> None:
    """About 1/mm at 780 nm and a resist path of the working distance (380 µm): ≈ 70 %."""
    k = kappa_from_alpha_per_mm(1.0, 0.78)
    p = focus_power_mW(58.0, kappa=k, wavelength_um=0.78, path_um=380.0)
    assert p / 58.0 == pytest.approx(math.exp(-0.38), rel=1e-12)
    assert abs(p / 58.0 - 0.70) < 0.03


def test_no_absorption_and_objective_transmission() -> None:
    assert focus_power_mW(20.0, kappa=0.0, wavelength_um=0.78, path_um=None) == 20.0
    assert (
        focus_power_mW(20.0, kappa=0.0, wavelength_um=0.78, path_um=None, t_objective=0.8) == 16.0
    )
    with pytest.raises(ValueError, match="resist_path_um"):
        focus_power_mW(20.0, kappa=1e-5, wavelength_um=0.78, path_um=None)


@pytest.mark.parametrize("a", [0.0, 0.38, 2.0])
@pytest.mark.parametrize("na_over_n", [0.3, 0.53, 0.9])
def test_cone_average_against_exponential_integrals(a: float, na_over_n: float) -> None:
    c = math.sqrt(1 - na_over_n**2)
    um = 1 / c
    if a == 0.0:
        expected = 1.0
    else:
        expected = 2 * (expn(3, a) - expn(3, a * um) / um**2) / na_over_n**2
    assert cone_transmission(a, na_over_n) == pytest.approx(expected, rel=1e-12)


def test_cone_average_first_order_and_size_of_the_effect() -> None:
    a, s = 1e-4, 0.8 / 1.52  # weak absorption, process A (NA 0.8, IP-Black n ≈ 1.52)
    c = math.sqrt(1 - s * s)
    assert 1 - cone_transmission(a, s) == pytest.approx(a * 2 / (1 + c), rel=1e-3)
    # process A: axial 0.684 vs cone average
    t_axis, t_cone = math.exp(-0.38), cone_transmission(0.38, s)
    assert t_cone < t_axis
    assert t_axis - t_cone == pytest.approx(0.0206, abs=5e-4)  # 68.4 % on axis, 66.3 % cone
