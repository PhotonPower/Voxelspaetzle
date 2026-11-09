"""V8a: tolerance analysis over the process scatter (spezifikation §3.13, Testfall P28)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from voxelspaetzle.dose import Grid, dose_field
from voxelspaetzle.fields import FieldGrid
from voxelspaetzle.focus import GaussFocus
from voxelspaetzle.path import KIND_HATCH, Job, Layer, Segments, WritePath
from voxelspaetzle.slicer import WriteParameters, slice_shell
from voxelspaetzle.threshold import line_size
from voxelspaetzle.tolerance import (
    FieldOffset,
    JobOffset,
    Perturbation,
    PowerNoise,
    monte_carlo,
    perturb,
)

FOCUS = GaussFocus(0.4, 1.2)


def segs(n: int, z: float = 0.0, x0: float = -8.0, length: float = 16.0) -> Segments:
    xs = x0 + length * np.arange(n) / n
    one = np.ones(n)
    return Segments(
        np.column_stack([xs, np.zeros(n), np.full(n, z)]),
        np.column_stack([xs + length / n, np.zeros(n), np.full(n, z)]),
        20.0 * one,
        1e3 * one,
        np.full(n, KIND_HATCH, dtype=np.int8),
        0.0 * one,
        np.zeros(n, dtype=np.int32),
        np.zeros(n, dtype=np.int32),
    )


def two_jobs() -> WritePath:
    return WritePath(
        "test",
        [
            Job("IP-S", [Layer(0.0, 0.0, segs(4)), Layer(0.5, 0.0, segs(4, 0.5))]),
            Job("IP-Black", [Layer(0.0, 0.0, segs(3))]),
        ],
    )


def test_no_scatter_leaves_the_path_unchanged() -> None:
    p = two_jobs()
    d = perturb(p, [PowerNoise(0.0), JobOffset((0.0, 0.0, 0.0))], np.random.default_rng(1))
    for a, b in zip(p.jobs, d.path.jobs, strict=True):
        for la, lb in zip(a.layers, b.layers, strict=True):
            assert la.segments.start_um.tobytes() == lb.segments.start_um.tobytes()
            assert la.segments.power_mW.tobytes() == lb.segments.power_mW.tobytes()


def test_draws_are_reproducible_and_recorded() -> None:
    p = two_jobs()
    pert: list[Perturbation] = [PowerNoise(0.05, "layer"), JobOffset((0.1, 0.1, 0.0))]
    a = perturb(p, pert, np.random.default_rng(7))
    b = perturb(p, pert, np.random.default_rng(7))
    c = perturb(p, pert, np.random.default_rng(8))
    assert a.values["job_offset_um"].tobytes() == b.values["job_offset_um"].tobytes()
    assert a.values["job_offset_um"].tobytes() != c.values["job_offset_um"].tobytes()
    assert p.jobs[0].layers[0].segments.power_mW[0] == 20.0  # input not modified


def test_job_offset_shifts_later_jobs_only() -> None:
    p = two_jobs()
    d = perturb(p, [JobOffset((0.2, 0.3, 0.05))], np.random.default_rng(3))
    off = d.values["job_offset_um"]
    assert np.all(off[0] == 0.0) and np.any(off[1] != 0.0)
    for j, job in enumerate(d.path.jobs):
        for la, lb in zip(p.jobs[j].layers, job.layers, strict=True):
            np.testing.assert_allclose(
                lb.segments.start_um - la.segments.start_um,
                np.broadcast_to(off[j], la.segments.start_um.shape),
                atol=1e-15,
            )
            np.testing.assert_allclose(
                lb.segments.end_um - la.segments.end_um,
                np.broadcast_to(off[j], la.segments.end_um.shape),
                atol=1e-15,
            )


def test_field_offset_moves_each_field_rigidly() -> None:
    body_params = WriteParameters(
        slicing_um=0.5, hatching_um=1.0, power_mW=10.0, speed_um_per_s=1e4
    )
    from bodies import Cylinder

    p = slice_shell(Cylinder(30.0, 1.0).shell(), body_params, "IP-S", fields=FieldGrid(25.0))
    d = perturb(p, [FieldOffset((0.1, 0.1))], np.random.default_rng(5))
    off = d.values["field_offset_um"][0]
    assert off.shape == (len(p.jobs[0].fields), 2)
    for la, lb in zip(p.jobs[0].layers, d.path.jobs[0].layers, strict=True):
        shift = lb.segments.start_um - la.segments.start_um
        np.testing.assert_allclose(shift[:, :2], off[la.segments.field], atol=1e-15)
        assert np.all(shift[:, 2] == 0.0)
        length_a = np.linalg.norm(la.segments.end_um - la.segments.start_um, axis=1)
        length_b = np.linalg.norm(lb.segments.end_um - lb.segments.start_um, axis=1)
        np.testing.assert_allclose(length_b, length_a, atol=1e-12)


@pytest.mark.parametrize("scope", ["segment", "layer", "job"])
def test_power_noise_scopes(scope: str) -> None:
    p = two_jobs()
    d = perturb(p, [PowerNoise(0.05, scope)], np.random.default_rng(11))
    f0 = d.path.jobs[0].layers[0].segments.power_mW / 20.0
    f1 = d.path.jobs[0].layers[1].segments.power_mW / 20.0
    g = d.path.jobs[1].layers[0].segments.power_mW / 20.0
    if scope == "segment":
        assert len(set(f0.tolist())) == f0.size
    if scope == "layer":
        assert len(set(f0.tolist())) == 1 and f0[0] != f1[0] and f0[0] != g[0]
    if scope == "job":
        assert len(set(np.r_[f0, f1].tolist())) == 1 and f0[0] != g[0]


def test_monte_carlo_line_width_matches_the_linear_theory() -> None:
    """σ_d/d ≈ (σ_P/P)/ln(D₀/D_th) for one power per line (§3.6, fischer2013 Abschn. 4.3)."""
    path = WritePath("test", [Job("IP-S", [Layer(0.0, 0.0, segs(1))])])
    grid = Grid((-0.55, -1.01, -2.025), (0.1, 0.02, 0.05), (81, 101, 11))
    d0 = 20.0**2 * (2 / (math.pi * 0.4**2)) ** 2 * (math.sqrt(math.pi) * 0.4 / 2) / 1e3
    d_th = 0.3 * d0

    def width(p: WritePath) -> float:
        return line_size(dose_field(p, grid, FOCUS), d_th, x_um=0.0).width_um

    mc = monte_carlo(path, [PowerNoise(0.02, "job")], width, n=60, seed=42)
    assert mc.samples.shape == (60,) and mc.seed == 42
    # the same draws again: each sample against the closed form w₀√(ln(f² D₀/D_th))
    rng = np.random.default_rng(42)
    f = np.array(
        [
            perturb(path, [PowerNoise(0.02, "job")], rng).values["power_factor_job"][0][0][0]
            for _ in range(60)
        ]
    )
    exact = 0.4 * np.sqrt(np.log(f**2 * d0 / d_th))
    # linear interpolation of the crossing: ≈ h²/8·|D''/D'| ≈ 3·10⁻⁴ µm per edge → 1.5·10⁻³
    np.testing.assert_allclose(mc.samples, exact, rtol=2e-3)
    # linear theory for the spread of these draws: σ_d/d ≈ σ_f/ln(D₀/D_th)
    assert mc.std / mc.mean == pytest.approx(np.std(f, ddof=1) / math.log(1 / 0.3), rel=0.02)
    again = monte_carlo(path, [PowerNoise(0.02, "job")], width, n=5, seed=42)
    assert again.samples.tobytes() == mc.samples[:5].tobytes()


def test_invalid_scatter() -> None:
    with pytest.raises(ValueError):
        PowerNoise(-0.1)
    with pytest.raises(ValueError):
        PowerNoise(0.1, "wafer")
    with pytest.raises(ValueError):
        JobOffset((-1.0, 0.0, 0.0))
