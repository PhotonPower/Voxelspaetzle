"""JSON envelope and array encoding (spezifikation §5)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from voxelspaetzle.envelope import dump, load


def test_roundtrip_is_bitwise(tmp_path: Path) -> None:
    data: dict[str, Any] = {
        "a": np.array([[0.1, -0.0, np.nan], [np.inf, -np.inf, 1e-300]]),
        "i": np.arange(5, dtype=np.int8),
        "c": np.array([1 + 2j, -0.5j]),
        "s": "text",
        "nested": [{"x": np.float64(0.1)}],
    }
    p = tmp_path / "f.json"
    dump(p, "voxelspaetzle-test", data)
    back = load(p, "voxelspaetzle-test")
    for k in ("a", "i", "c"):
        want = np.asarray(data[k])
        got = np.asarray(back[k])
        assert got.dtype == want.dtype and got.shape == want.shape
        assert got.tobytes() == want.tobytes() or (
            k == "a" and np.array_equal(got, want, equal_nan=True)
        )
    assert back["s"] == "text" and back["nested"][0]["x"] == 0.1
    text = p.read_text()
    assert "NaN" in text and json.loads(text)["format"] == "voxelspaetzle-test"


def test_large_arrays_go_to_npz(tmp_path: Path) -> None:
    big = np.random.default_rng(1).normal(size=(1200, 1000))
    p = tmp_path / "big.json"
    dump(p, "voxelspaetzle-test", {"big": big}, npz_threshold=1000)
    assert (tmp_path / "big.npz").exists()
    back = load(p, "voxelspaetzle-test")
    assert back["big"].tobytes() == big.tobytes()
    (tmp_path / "big.npz").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="SHA-256"):
        load(p, "voxelspaetzle-test")


def test_wrong_format_or_version(tmp_path: Path) -> None:
    p = tmp_path / "f.json"
    dump(p, "voxelspaetzle-path", {})
    with pytest.raises(ValueError):
        load(p, "voxelspaetzle-field")
    doc = json.loads(p.read_text())
    doc["schema_version"] = "1.0.0"
    p.write_text(json.dumps(doc))
    with pytest.raises(ValueError):
        load(p, "voxelspaetzle-path")
