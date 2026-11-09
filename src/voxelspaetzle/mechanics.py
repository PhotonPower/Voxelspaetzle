"""Shrinkage with linear elasticity on voxel hexahedra (spezifikation §3.8; D4 interim solver).

Every developed voxel (α ≥ α_dev) is a trilinear 8-node hexahedron with isotropic elasticity
(E, ν), integrated with 2×2×2 Gauss points. The eigenstrain is ε* = −s·α·I with the shrinkage s
of the fully polymerised resist; it enters as the load ∫ Bᵀ C ε* dV. Supports: ``substrate``
clamps all nodes of developed voxels on the plane z = z_sub; ``free`` removes the rigid-body
motions by a 3-2-1 support around the node next to the solid's centroid, which is consistent
with a homogeneous shrinkage about that node. Displacements do not depend on E.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import scipy.sparse as sp
from numpy.typing import NDArray
from scipy.sparse.linalg import cg

import voxelspaetzle
from voxelspaetzle import envelope
from voxelspaetzle.dose import Grid, VolumeField
from voxelspaetzle.threshold import HeightMap

FORMAT = "voxelspaetzle-displacement"
FloatArray = NDArray[np.float64]
_CORNERS = np.array(list(itertools.product((0, 1), repeat=3)))[:, ::-1]  # (dx, dy, dz)


@dataclass(frozen=True)
class Elastic:
    """Young's modulus (MPa), Poisson ratio, isotropic shrinkage s of the cured resist."""

    e_mpa: float
    nu: float
    shrinkage: float

    def __post_init__(self) -> None:
        if not (self.e_mpa > 0.0 and -1.0 < self.nu < 0.5):
            raise ValueError("need E > 0 and −1 < ν < 0.5")


def _c_matrix(e: float, nu: float) -> FloatArray:
    lam = e * nu / ((1 + nu) * (1 - 2 * nu))
    mu = e / (2 * (1 + nu))
    c = np.zeros((6, 6))
    c[:3, :3] = lam
    c[np.arange(3), np.arange(3)] += 2 * mu
    c[np.arange(3, 6), np.arange(3, 6)] = mu
    return c


def element_matrices(
    step: tuple[float, float, float], e: float, nu: float
) -> tuple[FloatArray, FloatArray]:
    """Stiffness K_e (24, 24) and load f_e (24,) for ε* = I of a brick hx × hy × hz.

    Local node order = ``_CORNERS`` (dx, dy, dz ∈ {0, 1}); DOF 3·node + component.
    """
    h = np.asarray(step, dtype=float)
    c = _c_matrix(e, nu)
    gp = 0.5 + np.array([-1.0, 1.0]) / (2 * np.sqrt(3.0))  # Gauss points on [0, 1]
    ke = np.zeros((24, 24))
    fe = np.zeros(24)
    unit = np.array([1.0, 1.0, 1.0, 0.0, 0.0, 0.0])
    vol = float(np.prod(h)) / 8.0
    for xi, eta, zeta in itertools.product(gp, gp, gp):
        q = np.array([xi, eta, zeta])
        b = np.zeros((6, 24))
        for a, corner in enumerate(_CORNERS):
            w = np.where(corner == 1, q, 1 - q)
            dn = np.array(
                [
                    (1 if corner[0] else -1) * w[1] * w[2] / h[0],
                    (1 if corner[1] else -1) * w[0] * w[2] / h[1],
                    (1 if corner[2] else -1) * w[0] * w[1] / h[2],
                ]
            )
            i = 3 * a
            b[0, i], b[1, i + 1], b[2, i + 2] = dn
            b[3, i], b[3, i + 1] = dn[1], dn[0]  # γ_xy
            b[4, i + 1], b[4, i + 2] = dn[2], dn[1]  # γ_yz
            b[5, i], b[5, i + 2] = dn[2], dn[0]  # γ_xz
        ke += b.T @ c @ b * vol
        fe += b.T @ (c @ unit) * vol
    return ke, fe


@dataclass
class Displacement:
    """Nodal displacements (nz+1, ny+1, nx+1, 3) in µm on the corners of the voxel grid."""

    grid: Grid
    u_um: FloatArray
    active: NDArray[np.bool_]
    reference_um: tuple[float, float, float] = (0.0, 0.0, 0.0)
    source: dict[str, Any] = field(default_factory=dict)

    def at(self, points_um: FloatArray) -> FloatArray:
        """Trilinear interpolation at points (N, 3) inside the grid."""
        p = np.asarray(points_um, dtype=float).reshape(-1, 3)
        h = np.asarray(self.grid.step_um)
        c = (p - np.asarray(self.grid.origin_um)) / h
        nz, ny, nx = self.grid.shape
        i0 = np.clip(np.floor(c).astype(int), 0, [nx - 1, ny - 1, nz - 1])
        f = c - i0
        out = np.zeros((p.shape[0], 3))
        for corner in _CORNERS:
            w = np.prod(np.where(corner == 1, f, 1 - f), axis=1)
            idx = i0 + corner
            out += w[:, None] * self.u_um[idx[:, 2], idx[:, 1], idx[:, 0]]
        return out

    def save(self, path: str | Path) -> None:
        envelope.dump(
            path,
            FORMAT,
            {
                "origin_um": list(self.grid.origin_um),
                "step_um": list(self.grid.step_um),
                "shape": list(self.grid.shape),
                "u_um": self.u_um,
                "active": self.active,
                "reference_um": list(self.reference_um),
                "source": self.source,
            },
        )

    @classmethod
    def load(cls, path: str | Path) -> Displacement:
        d = envelope.load(path, FORMAT)
        o, s, n = d["origin_um"], d["step_um"], d["shape"]
        grid = Grid((o[0], o[1], o[2]), (s[0], s[1], s[2]), (int(n[0]), int(n[1]), int(n[2])))
        r = d["reference_um"]
        return cls(grid, d["u_um"], d["active"], (r[0], r[1], r[2]), d["source"])


def solve_shrinkage(
    alpha_field: VolumeField,
    elastic: Elastic,
    support: str,
    substrate_z_um: float | None = None,
    alpha_dev: float = 0.5,
    rtol: float = 1e-12,
) -> Displacement:
    """Displacement of the developed part under the shrinkage eigenstrain (§3.8)."""
    if support not in ("substrate", "free"):
        raise ValueError('support must be "substrate" or "free"')
    g = alpha_field.grid
    alpha = np.asarray(alpha_field.data["alpha"], dtype=float)
    nz, ny, nx = alpha.shape
    solid = alpha >= alpha_dev
    ek, ei, ej = np.nonzero(solid)  # element indices (k, j, i)
    if ek.size == 0:
        raise ValueError("no developed voxel (α ≥ α_dev)")
    ke, fe = element_matrices(g.step_um, elastic.e_mpa, elastic.nu)
    nn = (nz + 1, ny + 1, nx + 1)

    def node(k: Any, j: Any, i: Any) -> Any:
        return (k * nn[1] + j) * nn[2] + i

    conn = np.stack([node(ek + dz, ei + dy, ej + dx) for dx, dy, dz in _CORNERS], axis=1)
    dofs = (3 * conn[:, :, None] + np.arange(3)).reshape(-1, 24)
    rows = np.repeat(dofs, 24, axis=1).ravel()
    cols = np.tile(dofs, (1, 24)).ravel()
    ndof = 3 * nn[0] * nn[1] * nn[2]
    k_glob = sp.csr_matrix((np.tile(ke.ravel(), ek.size), (rows, cols)), shape=(ndof, ndof))
    load = -elastic.shrinkage * alpha[ek, ei, ej]
    f = np.bincount(dofs.ravel(), weights=(load[:, None] * fe[None, :]).ravel(), minlength=ndof)
    active_nodes = np.zeros(nn[0] * nn[1] * nn[2], dtype=bool)
    active_nodes[conn.ravel()] = True
    fixed = np.zeros(ndof, dtype=bool)
    z_nodes = g.origin_um[2] + np.arange(nn[0]) * g.step_um[2]
    reference = (0.0, 0.0, 0.0)
    if support == "substrate":
        if substrate_z_um is None:
            raise ValueError("support 'substrate' needs substrate_z_um")
        kz = np.flatnonzero(np.abs(z_nodes - substrate_z_um) < 1e-9 * max(g.step_um))
        on = np.zeros(nn, dtype=bool)
        on[kz] = True
        clamp = on.ravel() & active_nodes
        if not clamp.any():
            raise ValueError("no developed voxel touches the substrate plane")
        fixed[(3 * np.flatnonzero(clamp)[:, None] + np.arange(3)).ravel()] = True
    else:
        coords = np.stack(
            np.meshgrid(
                z_nodes,
                g.origin_um[1] + np.arange(nn[1]) * g.step_um[1],
                g.origin_um[0] + np.arange(nn[2]) * g.step_um[0],
                indexing="ij",
            ),
            axis=-1,
        ).reshape(-1, 3)[:, ::-1]
        act = np.flatnonzero(active_nodes)
        centroid = coords[act].mean(axis=0)
        p = act[np.argmin(np.linalg.norm(coords[act] - centroid, axis=1))]
        pk, pj, pi = np.unravel_index(p, nn)
        same_row = act[[np.unravel_index(n, nn)[:2] == (pk, pj) for n in act]]
        same_col = act[
            [(np.unravel_index(n, nn)[0], np.unravel_index(n, nn)[2]) == (pk, pi) for n in act]
        ]
        q = same_row[np.argmax(coords[same_row, 0])]
        r = same_col[np.argmax(coords[same_col, 1])]
        if q == p or r == p:
            raise ValueError("free support needs extent in x and y through the reference node")
        fixed[[3 * p, 3 * p + 1, 3 * p + 2, 3 * q + 1, 3 * q + 2, 3 * r + 2]] = True
        reference = (float(coords[p, 0]), float(coords[p, 1]), float(coords[p, 2]))
    free = np.repeat(active_nodes, 3) & ~fixed
    kff = k_glob[free][:, free]
    diag = kff.diagonal()
    m = sp.diags(1.0 / diag)
    sol, info = cg(kff, f[free], rtol=rtol, atol=0.0, M=m, maxiter=20 * kff.shape[0])
    if info != 0:
        raise RuntimeError(f"CG did not converge (info = {info})")
    u = np.zeros(ndof)
    u[free] = sol
    source = {
        "program": "voxelspaetzle",
        "version": voxelspaetzle.__version__,
        "elastic": {"e_mpa": elastic.e_mpa, "nu": elastic.nu, "shrinkage": elastic.shrinkage},
        "support": support,
        "substrate_z_um": substrate_z_um,
        "alpha_dev": alpha_dev,
    }
    return Displacement(g, u.reshape(*nn, 3), active_nodes.reshape(nn), reference, source)


def deformed_height_map(hm: HeightMap, d: Displacement) -> HeightMap:
    """Height map after shrinkage: z' = z + u_z(x, y, z) (lateral shift neglected, first order)."""
    ny, nx = hm.z_um.shape
    x = hm.origin_um[0] + np.arange(nx) * hm.step_um[0]
    y = hm.origin_um[1] + np.arange(ny) * hm.step_um[1]
    xx, yy = np.meshgrid(x, y)
    ok = ~np.isnan(hm.z_um)
    pts = np.column_stack([xx[ok], yy[ok], hm.z_um[ok]])
    z = hm.z_um.copy()
    z[ok] = hm.z_um[ok] + d.at(pts)[:, 2]
    return HeightMap(
        hm.origin_um,
        hm.step_um,
        z,
        hm.material_below,
        hm.material_above,
        hm.clipped,
        {**hm.source, "deformed_by": d.source},
    )
