import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from transport_analysis.explainer import ModelExplainer


def test_model_explainer_shap_fallback_and_summary():
    # small dataset
    X = pd.DataFrame({'a': [0.1, 0.2, 0.3], 'b': [1.0, 0.5, -0.2]})
    y = np.array([0.2, 0.1, 0.0])
    rf = RandomForestRegressor(n_estimators=10, random_state=0)
    rf.fit(X, y)

    expl = ModelExplainer(rf, feature_names=['a', 'b'])
    sv = expl.calculate_shap_values(X)
    # shap fallback returns zeros with shape (n_samples, n_features)
    arr = np.asarray(sv)
    assert arr.ndim in (2, 3)

    df = expl.get_feature_impact_summary(X)
    assert 'feature' in df.columns
    assert 'mean_abs_shap' in df.columns
