"""Process library ``voxelspaetzle-process`` (spezifikation §5.1).

A process describes printer, objective, mode, resists with named parameter sets, development and
post-processing, with the sources of every value. Values a source does not state are ``null``;
asking for a parameter set with such a value raises instead of inventing a number.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Any

from voxelspaetzle import envelope
from voxelspaetzle.focus import GaussFocus
from voxelspaetzle.slicer import WriteParameters

FORMAT = "voxelspaetzle-process"
MODES = ("dip_in_wrapped", "dip_in", "oil")
_REQUIRED = ("slicing_um", "hatching_um", "speed_um_per_s")


@dataclass
class Process:
    name: str
    printer: dict[str, Any]
    objective: dict[str, Any]
    mode: str
    resist_path_um: float | None
    polarization: str | None
    focus: dict[str, Any]
    resists: dict[str, dict[str, Any]]
    development: list[dict[str, Any]] = field(default_factory=list)
    postprocess: list[dict[str, Any]] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    notes: str = ""

    def __post_init__(self) -> None:
        if self.mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}")

    def write_parameters(self, resist: str, parameter_set: str) -> WriteParameters:
        """Write parameters of a named set; power from ``power_mW`` or ``power_percent``."""
        s = dict(self.resists[resist]["parameter_sets"][parameter_set])
        power = s.pop("power_mW", None)
        percent = s.pop("power_percent", None)
        full = self.printer.get("power_100pct_mW")
        if power is None and percent is not None and full is not None:
            power = percent / 100.0 * full
        missing = [k for k in _REQUIRED if s.get(k) is None]
        if power is None:
            missing.append("power")
        if missing:
            where = f"{self.name}: {resist}/{parameter_set}"
            raise ValueError(f"{where}: {', '.join(missing)} not given in the sources")
        s.pop("notes", None)
        for key in ("hatch_angle_deg", "hatch_angle_step_deg"):
            if key in s:
                s[key.replace("_deg", "_rad")] = math.radians(s.pop(key))
        return WriteParameters(power_mW=float(power), **s)

    def focus_kernel(self) -> GaussFocus:
        """Focus kernel of the process (§3.2; Gaussian until D8)."""
        if self.focus.get("kind") != "gauss":
            raise ValueError(f"{self.name}: focus kind {self.focus.get('kind')!r} not supported")
        w0, wz = self.focus.get("w0_um"), self.focus.get("wz_um")
        if w0 is None or wz is None:
            raise ValueError(f"{self.name}: focus half-axes w0_um, wz_um not given in the sources")
        return GaussFocus(float(w0), float(wz))

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}

    def save(self, path: str | Path) -> None:
        envelope.dump(path, FORMAT, self.to_dict())


def _builtin(name: str) -> Path | None:
    f = resources.files("voxelspaetzle") / "processes" / f"{name}.json"
    return Path(str(f)) if f.is_file() else None


def list_processes() -> list[str]:
    """Names of the processes shipped with the package."""
    d = resources.files("voxelspaetzle") / "processes"
    return sorted(p.name.removesuffix(".json") for p in d.iterdir() if p.name.endswith(".json"))


def load_process(name_or_path: str | Path) -> Process:
    """A shipped process by name, or a process file."""
    path = _builtin(str(name_or_path)) if isinstance(name_or_path, str) else None
    data = envelope.load(path or Path(name_or_path), FORMAT)
    return Process(**data)
