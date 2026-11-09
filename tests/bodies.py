"""Analytic test bodies built with Nurbforge (µm), with their exact reference values."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import nurbforge as nf


@dataclass(frozen=True)
class Cylinder:
    """Circular cylinder of radius r_um on the substrate, from z = 0 to z = h_um."""

    r_um: float
    h_um: float

    def shell(self) -> Any:
        side = nf.extrude(nf.make_circle((0, 0, 0), (0, 0, 1), self.r_um), (0, 0, self.h_um))
        r = self.r_um
        lids = [
            nf.TrimmedSurface(
                nf.make_rectangle((-r, -r, z), (2 * r, 0, 0), (0, 2 * r, 0)),
                nf.circle_loop(0.5, 0.5, 0.5),
            )
            for z in (0.0, self.h_um)
        ]
        return nf.Shell.sew([nf.TrimmedSurface(side), *lids]).oriented()

    def radius_at(self, z_um: float) -> float:
        return self.r_um if 0.0 < z_um < self.h_um else 0.0

    def volume(self) -> float:
        return math.pi * self.r_um**2 * self.h_um


@dataclass(frozen=True)
class SphericalCap:
    """Spherical cap (plano-convex lens) of sphere radius R_um and height h_um on z = 0."""

    big_r_um: float
    h_um: float

    @property
    def base_radius_um(self) -> float:
        return math.sqrt(2 * self.big_r_um * self.h_um - self.h_um**2)

    def shell(self) -> Any:
        big_r, h, a = self.big_r_um, self.h_um, self.base_radius_um
        arc = nf.make_arc((0, 0, h - big_r), (0, 0, 1), (1, 0, 0), big_r, 0.0, math.asin(a / big_r))
        dome = nf.revolve(arc, (0, 0, 0), (0, 0, 1), 2 * math.pi)
        base = nf.TrimmedSurface(
            nf.make_rectangle((-a, -a, 0), (2 * a, 0, 0), (0, 2 * a, 0)),
            nf.circle_loop(0.5, 0.5, 0.5),
        )
        return nf.Shell.sew([nf.TrimmedSurface(dome), base]).oriented()

    def radius_at(self, z_um: float) -> float:
        if not 0.0 < z_um < self.h_um:
            return 0.0
        zc = self.h_um - self.big_r_um
        return math.sqrt(self.big_r_um**2 - (z_um - zc) ** 2)

    def volume(self) -> float:
        """π h² (3R − h)/3."""
        return math.pi * self.h_um**2 * (3 * self.big_r_um - self.h_um) / 3


@dataclass(frozen=True)
class Ring:
    """Cylinder with a coaxial hole (outer r_um, inner ri_um, height h_um)."""

    r_um: float
    ri_um: float
    h_um: float

    def shell(self) -> Any:
        outer = Cylinder(self.r_um, self.h_um).shell()
        side = nf.extrude(
            nf.make_circle((0, 0, -1.0), (0, 0, 1), self.ri_um), (0, 0, self.h_um + 2.0)
        )
        ri = self.ri_um
        lids = [
            nf.TrimmedSurface(
                nf.make_rectangle((-ri, -ri, z), (2 * ri, 0, 0), (0, 2 * ri, 0)),
                nf.circle_loop(0.5, 0.5, 0.5),
            )
            for z in (-1.0, self.h_um + 1.0)
        ]
        inner = nf.Shell.sew([nf.TrimmedSurface(side), *lids]).oriented()
        return nf.boolean(outer, inner, nf.BooleanOp.Difference)

    def volume(self) -> float:
        return math.pi * (self.r_um**2 - self.ri_um**2) * self.h_um
