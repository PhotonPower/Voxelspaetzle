"""Developer access (spezifikation §3.8, Testfall P16).

Liquid resist (α < α_dev) is washed out if a face-connected path of liquid voxels leads to the
outside of the grid; on a substrate the bottom face is closed. Liquid without such a path stays
enclosed (trapped). A path of one voxel already counts as open; minimum opening widths and
development times are not modelled.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from scipy import ndimage

from voxelspaetzle.dose import VolumeField


def trapped_liquid(
    alpha_field: VolumeField, substrate: bool = True, alpha_dev: float = 0.5
) -> NDArray[np.bool_]:
    """Mask (z, y, x) of liquid voxels the developer cannot reach."""
    liquid = np.asarray(alpha_field.data["alpha"], dtype=float) < alpha_dev
    labels, n = ndimage.label(liquid)  # face connectivity in 3D
    border = np.zeros(liquid.shape, dtype=bool)
    border[-1], border[:, 0], border[:, -1], border[:, :, 0], border[:, :, -1] = (True,) * 5
    if not substrate:
        border[0] = True
    open_labels = np.unique(labels[border & liquid])
    out: NDArray[np.bool_] = liquid & ~np.isin(labels, open_labels)
    return out
