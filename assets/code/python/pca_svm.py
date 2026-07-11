from __future__ import annotations

import numpy as np
from sklearn.decomposition import PCA
from sklearn.metrics import accuracy_score, classification_report
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC


def fit_pca_svm(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray | None = None,
    y_test: np.ndarray | None = None,
    n_components: int | float = 0.95,
    c_value: float = 1.0,
    kernel: str = "rbf",
) -> dict[str, object]:
    """Fit a PCA plus SVM classification pipeline."""
    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("pca", PCA(n_components=n_components)),
            ("svm", SVC(C=c_value, kernel=kernel)),
        ]
    )
    pipeline.fit(x_train, y_train)
    result: dict[str, object] = {"model": pipeline}

    if x_test is not None and y_test is not None:
        predictions = pipeline.predict(x_test)
        result["predictions"] = predictions
        result["accuracy"] = accuracy_score(y_test, predictions)
        result["report"] = classification_report(y_test, predictions, output_dict=True)

    return result
