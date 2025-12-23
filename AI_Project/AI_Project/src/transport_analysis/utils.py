import numpy as np


def align_shap_with_features(shap_vals, X):
    """Ensure SHAP output matches X shape: (n_samples, n_features).

    Handles lists (per-class), 2D arrays and 3D arrays with class dim.
    """
    X_arr = np.asarray(X)
    n_samples = X_arr.shape[0]

    if isinstance(shap_vals, list):
        aligned = []
        for v in shap_vals:
            v = np.asarray(v)
            if v.ndim == 2 and v.shape[0] != n_samples and v.shape[1] == n_samples:
                v = v.T
            elif v.ndim == 3 and v.shape[1] == n_samples:
                v = v.transpose(0, 2, 1)
            aligned.append(v)
        return aligned

    a = np.asarray(shap_vals)
    if a.ndim == 2:
        if a.shape[0] != n_samples and a.shape[1] == n_samples:
            return a.T
    elif a.ndim == 3:
        if a.shape[2] == n_samples and a.shape[1] != n_samples:
            return a.transpose(0, 2, 1)
    return a
