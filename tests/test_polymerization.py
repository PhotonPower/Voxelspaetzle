"""V4a: degree of polymerisation, material data and the (n, κ) field (spezifikation §3.7, §5.6)."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray

from voxelspaetzle.dose import Grid, VolumeField
from voxelspaetzle.materials import Material, list_materials, load_material
from voxelspaetzle.polymerization import ThresholdModel, degree_of_polymerization, optical_field
from voxelspaetzle.threshold import solid_field

# schmid2023, Sellmeier fit of the polymerised IP-Black (standard form with B3, issue #9)
B = (1.03051, 2.20788e-1, 1.00968)
C = (4.92832e-3, 3.002e-2, 1.03560e2)


def sellmeier(lam: float) -> float:
    l2 = lam * lam
    return math.sqrt(1 + sum(b * l2 / (l2 - c) for b, c in zip(B, C, strict=True)))


def dose_cube() -> VolumeField:
    grid = Grid(origin_um=(0.0, 0.0, 0.0), step_um=(1.0, 1.0, 1.0), shape=(3, 4, 5))
    d = np.arange(60, dtype=float).reshape(3, 4, 5)
    return VolumeField(grid, {"dose_mW2s_per_um4": d}, {"kind": "gauss"}, {"program": "test"})


def test_ip_black_is_shipped() -> None:
    assert "IP-Black" in list_materials()


@pytest.mark.parametrize("lam", [0.4, 0.5876, 0.78, 0.9])
def test_cured_index_is_the_sellmeier_fit(lam: float) -> None:
    m = load_material("IP-Black")
    assert m.n(lam, alpha=1.0) == pytest.approx(sellmeier(lam), abs=1e-12)


def test_liquid_index_matches_the_measured_range() -> None:
    m = load_material("IP-Black")
    assert m.n(0.4, alpha=0.0) == pytest.approx(1.505, abs=5e-3)
    assert m.n(0.9, alpha=0.0) == pytest.approx(1.48, abs=5e-3)
    assert m.n(0.6, 1.0) - m.n(0.6, 0.0) == pytest.approx(0.02, abs=1e-12)


def test_interpolation_in_alpha_is_linear() -> None:
    m = load_material("IP-Black")
    a = np.array([0.0, 0.25, 1.0])
    n = m.n(0.6, a)
    np.testing.assert_allclose(n, m.n(0.6, 0.0) + a * (m.n(0.6, 1.0) - m.n(0.6, 0.0)), atol=1e-15)


def test_absorption_at_the_writing_wavelength() -> None:
    m = load_material("IP-Black")
    assert m.kappa(0.78, alpha=1.0) == pytest.approx(1.0 * 0.78e-3 / (4 * math.pi), rel=1e-12)


def test_values_not_in_the_sources_are_refused() -> None:
    m = load_material("IP-Black")
    with pytest.raises(ValueError, match="not given"):
        m.kappa(0.55, alpha=1.0)  # visible absorption only as a figure in schmid2023
    with pytest.raises(ValueError, match="range"):
        m.n(1.2, alpha=1.0)  # outside the measured 0.4 … 0.9 µm


def test_threshold_limit_equals_the_solid_mask() -> None:
    """P6: without diffusion and with instant reaction, α is the threshold solid."""
    f = dose_cube()
    alpha = degree_of_polymerization(f, ThresholdModel(d_th=29.5)).data["alpha"]
    mask = solid_field(f, 29.5, "IP-Black").data["material"]
    np.testing.assert_array_equal(alpha, mask.astype(float))


def test_optical_field_developed_and_in_the_liquid() -> None:
    f = dose_cube()
    alpha = degree_of_polymerization(f, ThresholdModel(d_th=29.5))
    m = load_material("IP-Black")
    with pytest.raises(ValueError, match="not given"):
        optical_field(alpha, m, [0.6, 0.78], developed=True)  # κ at 0.6 µm unknown
    dev = optical_field(
        alpha, m, [0.6, 0.78], developed=True, surrounding=("air", 1.0), missing_kappa="nan"
    )
    assert dev.data["kappa_missing_um"] == [0.6]
    assert np.isnan(dev.data["kappa"][0][a_solid(alpha)]).all()
    n = dev.data["n"]
    assert n.shape == (2, 3, 4, 5) and dev.data["wavelengths_um"] == [0.6, 0.78]
    a = alpha.data["alpha"]
    np.testing.assert_allclose(n[0][a == 1.0], m.n(0.6, 1.0), atol=0)
    np.testing.assert_allclose(n[0][a == 0.0], 1.0, atol=0)
    assert dev.data["materials"] == ["air", "IP-Black"]
    assert dev.data["kappa"][1][a == 1.0] == pytest.approx(m.kappa(0.78, 1.0))
    liq = optical_field(alpha, m, [0.78], developed=False)
    np.testing.assert_allclose(liq.data["n"][0][a == 0.0], m.n(0.78, 0.0), atol=0)
    with pytest.raises(ValueError, match="not given"):
        optical_field(alpha, m, [0.55], developed=True)


def a_solid(alpha: VolumeField) -> NDArray[np.bool_]:
    out: NDArray[np.bool_] = np.asarray(alpha.data["alpha"]) == 1.0
    return out


def test_material_file_roundtrip(tmp_path: Path) -> None:
    m = load_material("IP-Black")
    m.save(tmp_path / "m.json")
    assert load_material(tmp_path / "m.json") == m
    assert isinstance(m, Material) and "schmid2023" in m.sources
