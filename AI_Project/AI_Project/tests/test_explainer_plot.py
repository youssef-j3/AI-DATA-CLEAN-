import numpy as np
import pandas as pd
from transport_analysis.explainer import ModelExplainer
from sklearn.ensemble import RandomForestRegressor


def test_plot_shap_summary_falls_back():
    # create synthetic data
    X = pd.DataFrame({'f1': np.random.randn(50), 'f2': np.random.randn(50)})
    y = X['f1'] * 0.5 - X['f2'] * 0.2 + np.random.randn(50) * 0.1
    model = RandomForestRegressor(n_estimators=10, random_state=0)
    model.fit(X, y)
    expl = ModelExplainer(model, feature_names=list(X.columns))
    plt_obj = expl.plot_shap_summary(X, max_display=5)
    # should return a matplotlib.pyplot module-like object with tight_layout attribute
    assert hasattr(plt_obj, 'tight_layout')
