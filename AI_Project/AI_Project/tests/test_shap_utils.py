import numpy as np
from transport_analysis.utils import align_shap_with_features


def test_align_2d_transpose():
    X = np.zeros((5, 3))
    shap = np.zeros((3, 5))  # (features, samples) should transpose
    aligned = align_shap_with_features(shap, X)
    assert aligned.shape == (5, 3)


def test_align_3d_transpose():
    X = np.zeros((4, 2))
    # shape (n_classes, n_features, n_samples)
    shap = np.zeros((2, 3, 4))
    aligned = align_shap_with_features(shap, X)
    assert aligned.shape == (2, 4, 3)


def test_list_of_arrays():
    X = np.zeros((6, 2))
    s1 = np.zeros((2, 6))
    s2 = np.zeros((6, 2))
    aligned = align_shap_with_features([s1, s2], X)
    assert isinstance(aligned, list) and len(aligned) == 2
    assert aligned[0].shape == (6, 2)
    assert aligned[1].shape == (6, 2)
