from __future__ import annotations

from typing import Sequence

import numpy as np
from sklearn.metrics import accuracy_score
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC


def _score_particle(
    particle: np.ndarray,
    x_train: np.ndarray,
    y_train: np.ndarray,
    cv_splits: int,
) -> float:
    c_value = 10 ** particle[0]
    gamma_value = 10 ** particle[1]
    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("svm", SVC(C=c_value, gamma=gamma_value, kernel="rbf")),
        ]
    )
    cv = StratifiedKFold(n_splits=cv_splits, shuffle=True, random_state=42)
    return float(cross_val_score(pipeline, x_train, y_train, cv=cv, scoring="accuracy").mean())


def svm_pso(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray | None = None,
    y_test: np.ndarray | None = None,
    bounds: Sequence[tuple[float, float]] = ((-2, 3), (-4, 1)),
    particles: int = 20,
    iterations: int = 30,
    inertia: float = 0.7,
    cognitive: float = 1.5,
    social: float = 1.5,
    cv_splits: int = 5,
    seed: int | None = 42,
) -> dict[str, object]:
    """Tune RBF-SVM hyperparameters with particle swarm search."""
    rng = np.random.default_rng(seed)
    bounds_array = np.asarray(bounds, dtype=float)
    lower = bounds_array[:, 0]
    upper = bounds_array[:, 1]
    span = upper - lower

    positions = rng.uniform(lower, upper, size=(particles, 2))
    velocities = rng.uniform(-span, span, size=(particles, 2))
    personal_best_positions = positions.copy()
    personal_best_scores = np.array(
        [_score_particle(position, x_train, y_train, cv_splits) for position in positions],
        dtype=float,
    )
    best_idx = int(np.argmax(personal_best_scores))
    global_best_position = personal_best_positions[best_idx].copy()
    global_best_score = float(personal_best_scores[best_idx])
    history = [global_best_score]

    for _ in range(iterations):
        r1 = rng.random((particles, 2))
        r2 = rng.random((particles, 2))
        velocities = (
            inertia * velocities
            + cognitive * r1 * (personal_best_positions - positions)
            + social * r2 * (global_best_position - positions)
        )
        positions = np.clip(positions + velocities, lower, upper)

        scores = np.array(
            [_score_particle(position, x_train, y_train, cv_splits) for position in positions],
            dtype=float,
        )
        improved = scores > personal_best_scores
        personal_best_positions[improved] = positions[improved]
        personal_best_scores[improved] = scores[improved]

        best_idx = int(np.argmax(personal_best_scores))
        global_best_position = personal_best_positions[best_idx].copy()
        global_best_score = float(personal_best_scores[best_idx])
        history.append(global_best_score)

    best_c = 10 ** global_best_position[0]
    best_gamma = 10 ** global_best_position[1]
    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("svm", SVC(C=best_c, gamma=best_gamma, kernel="rbf")),
        ]
    )
    model.fit(x_train, y_train)

    result: dict[str, object] = {
        "model": model,
        "best_params": {"C": best_c, "gamma": best_gamma},
        "best_cv_score": global_best_score,
        "history": np.asarray(history),
    }

    if x_test is not None and y_test is not None:
        predictions = model.predict(x_test)
        result["predictions"] = predictions
        result["test_accuracy"] = accuracy_score(y_test, predictions)

    return result
