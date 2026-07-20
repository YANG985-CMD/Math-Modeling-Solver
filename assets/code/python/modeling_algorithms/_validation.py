from __future__ import annotations

import numpy as np


def as_matrix(value: object, *, name: str = "matrix") -> np.ndarray:
    matrix = np.asarray(value, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] < 2 or matrix.shape[1] < 1:
        raise ValueError(f"{name} must be a 2-D array with at least two rows.")
    if not np.isfinite(matrix).all():
        raise ValueError(f"{name} contains non-finite values.")
    return matrix


def as_vector(value: object, *, name: str = "vector") -> np.ndarray:
    vector = np.asarray(value, dtype=float).reshape(-1)
    if vector.size == 0 or not np.isfinite(vector).all():
        raise ValueError(f"{name} must contain at least one finite value.")
    return vector


def benefit_flags(value: object | None, size: int) -> np.ndarray:
    if value is None:
        return np.ones(size, dtype=bool)
    flags = np.asarray(value, dtype=bool).reshape(-1)
    if flags.size != size:
        raise ValueError("benefit_mask length must match the number of criteria.")
    return flags
