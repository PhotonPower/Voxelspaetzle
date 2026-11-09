"""JSON envelope with array encoding (spezifikation §5).

Layout as Raytatouille's ``raytatouille-result`` (ADR 0023): ``{"format", "schema_version",
"data"}``; arrays as ``{"dtype", "shape", "values"}`` in C order, non-finite floats as the strings
``"NaN"``, ``"Infinity"``, ``"-Infinity"``, complex numbers as ``[re, im]``. Arrays with more than
``npz_threshold`` values go to a ``.npz`` file next to the JSON file and are referenced by
``{"npz", "key", "sha256"}`` (SHA-256 of the ``.npz`` file).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

SCHEMA_VERSION = "0.1.0"
_NONFINITE = {"NaN": np.nan, "Infinity": np.inf, "-Infinity": -np.inf}


def _float(x: float) -> float | str:
    if np.isnan(x):
        return "NaN"
    if np.isinf(x):
        return "Infinity" if x > 0 else "-Infinity"
    return float(x)


def _encode_array(a: NDArray[Any]) -> dict[str, Any]:
    flat = a.ravel(order="C")
    values: list[Any]
    if np.issubdtype(a.dtype, np.complexfloating):
        values = [[_float(z.real), _float(z.imag)] for z in flat]
    elif np.issubdtype(a.dtype, np.floating):
        values = [_float(x) for x in flat]
    elif a.dtype == np.bool_:
        values = [bool(x) for x in flat]
    elif np.issubdtype(a.dtype, np.integer):
        values = [int(x) for x in flat]
    else:
        raise ValueError(f"unsupported dtype {a.dtype}")
    return {"dtype": a.dtype.str, "shape": list(a.shape), "values": values}


def _decode_array(d: Mapping[str, Any]) -> NDArray[Any]:
    dtype = np.dtype(d["dtype"])
    shape = tuple(int(s) for s in d["shape"])
    vals = d["values"]
    if np.issubdtype(dtype, np.complexfloating):
        re = [_NONFINITE.get(v[0], v[0]) if isinstance(v[0], str) else v[0] for v in vals]
        im = [_NONFINITE.get(v[1], v[1]) if isinstance(v[1], str) else v[1] for v in vals]
        out = np.array(re, dtype=np.float64) + 1j * np.array(im, dtype=np.float64)
        return out.astype(dtype).reshape(shape)
    if np.issubdtype(dtype, np.floating):
        vals = [_NONFINITE[v] if isinstance(v, str) else v for v in vals]
    return np.array(vals, dtype=dtype).reshape(shape)


def _encode(obj: Any, big: dict[str, NDArray[Any]], threshold: int) -> Any:
    if isinstance(obj, np.ndarray):
        if obj.size > threshold:
            key = f"a{len(big)}"
            big[key] = np.ascontiguousarray(obj)
            return {"npz": None, "key": key}
        return _encode_array(obj)
    if isinstance(obj, np.generic):
        return _encode(obj.item(), big, threshold)
    if isinstance(obj, float):
        return {"float": _float(obj)} if not np.isfinite(obj) else obj
    if isinstance(obj, complex):
        return {"complex": [_float(obj.real), _float(obj.imag)]}
    if isinstance(obj, Mapping):
        return {str(k): _encode(v, big, threshold) for k, v in obj.items()}
    if isinstance(obj, list | tuple):
        return [_encode(v, big, threshold) for v in obj]
    return obj


def _decode(obj: Any, npz: Mapping[str, NDArray[Any]] | None) -> Any:
    if isinstance(obj, dict):
        if set(obj) == {"dtype", "shape", "values"}:
            return _decode_array(obj)
        if set(obj) == {"npz", "key", "sha256"}:
            if npz is None:
                raise ValueError("array reference without .npz file")
            return np.array(npz[obj["key"]])
        if set(obj) == {"float"}:
            v = obj["float"]
            return float(_NONFINITE[v]) if isinstance(v, str) else float(v)
        if set(obj) == {"complex"}:
            re, im = (
                float(_NONFINITE[v]) if isinstance(v, str) else float(v) for v in obj["complex"]
            )
            return complex(re, im)
        return {k: _decode(v, npz) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decode(v, npz) for v in obj]
    return obj


def _fill_refs(obj: Any, name: str, sha: str) -> Any:
    if isinstance(obj, dict):
        if set(obj) == {"npz", "key"}:
            return {"npz": name, "key": obj["key"], "sha256": sha}
        return {k: _fill_refs(v, name, sha) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_fill_refs(v, name, sha) for v in obj]
    return obj


def dump(
    path: str | Path, fmt: str, data: Mapping[str, Any], npz_threshold: int = 1_000_000
) -> None:
    """Write ``data`` as envelope ``fmt``; large arrays into ``<stem>.npz`` beside ``path``."""
    path = Path(path)
    big: dict[str, NDArray[Any]] = {}
    encoded = _encode(data, big, npz_threshold)
    if big:
        npz_path = path.with_suffix(".npz")
        np.savez(npz_path, **big)  # type: ignore[arg-type]
        sha = hashlib.sha256(npz_path.read_bytes()).hexdigest()
        encoded = _fill_refs(encoded, npz_path.name, sha)
    doc = {"format": fmt, "schema_version": SCHEMA_VERSION, "data": encoded}
    path.write_text(json.dumps(doc, allow_nan=False), encoding="utf-8")


def _refs(obj: Any) -> list[dict[str, str]]:
    if isinstance(obj, dict):
        if set(obj) == {"npz", "key", "sha256"}:
            return [obj]
        return [r for v in obj.values() for r in _refs(v)]
    if isinstance(obj, list):
        return [r for v in obj for r in _refs(v)]
    return []


def load(path: str | Path, fmt: str) -> Any:
    """Read an envelope of format ``fmt`` (schema 0.1.x) and decode its data."""
    path = Path(path)
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("format") != fmt:
        raise ValueError(f"expected format {fmt!r}, got {doc.get('format')!r}")
    if not str(doc.get("schema_version", "")).startswith("0.1."):
        raise ValueError(f"unsupported schema_version {doc.get('schema_version')!r}")
    refs = _refs(doc["data"])
    npz = None
    if refs:
        names = {r["npz"] for r in refs}
        if len(names) != 1:
            raise ValueError("array references to more than one .npz file")
        npz_path = path.parent / names.pop()
        sha = hashlib.sha256(npz_path.read_bytes()).hexdigest()
        if any(r["sha256"] != sha for r in refs):
            raise ValueError(f"SHA-256 of {npz_path.name} does not match the envelope")
        with np.load(npz_path) as f:
            npz = {k: f[k] for k in f.files}
    return _decode(doc["data"], npz)
