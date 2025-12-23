import os
import pandas as pd
import numpy as np
from transport_analysis.model_builder import ModelBuilder


def test_run_all_models_and_comparison():
    # create small synthetic dataset
    np.random.seed(0)
    df = pd.DataFrame({
        'f1': np.random.randn(100),
        'f2': np.random.randn(100) * 2,
    })
    # simple linear-ish target
    df['delay_minutes'] = 1.5 * df['f1'] - 0.5 * df['f2'] + np.random.randn(100) * 0.1

    mb = ModelBuilder(df)
    results = mb.run_all_models()
    assert 'RandomForest' in results
    assert 'LinearRegression' in results
    comp = mb.get_model_comparison()
    assert 'Model' in comp.columns
    assert comp['Model'].str.contains('RandomForest').any()
    assert comp['Model'].str.contains('LinearRegression').any()
    # metrics should be finite numbers
    row = comp[comp['Model'] == 'RandomForest'].iloc[0]
    assert float(row['Test R²']) >= -1.0
    assert float(row['Test MAE']) >= 0.0
    assert float(row['Test RMSE']) >= 0.0


def test_get_best_model_returns_model():
    np.random.seed(1)
    df = pd.DataFrame({'f1': np.random.randn(50), 'delay_minutes': np.random.randn(50)})
    mb = ModelBuilder(df)
    mb.run_all_models()
    name, model = mb.get_best_model()
    assert name is not None and model is not None


def test_save_and_load_model(tmp_path):
    np.random.seed(2)
    df = pd.DataFrame({'f1': np.random.randn(50), 'delay_minutes': np.random.randn(50)})
    mb = ModelBuilder(df)
    mb.run_all_models()
    name, model = mb.get_best_model()
    model_path = tmp_path / "rf_model.joblib"
    saved = mb.save_model(name, str(model_path))
    assert os.path.exists(saved)
    loaded = ModelBuilder.load_model(str(model_path))
    assert hasattr(loaded, 'predict')
    os.remove(saved)
