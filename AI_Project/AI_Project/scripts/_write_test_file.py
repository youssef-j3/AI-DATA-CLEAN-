content = '''import pandas as pd
import numpy as np
from transport_analysis.model_builder import ModelBuilder


def test_temporal_holdout_splits_and_metrics(tmp_path):
    # create synthetic data with a time column and a simple signal
    dates = pd.date_range(start='2020-01-01', periods=20, freq='D')
    df = pd.DataFrame({
        'scheduled_time': dates.astype(str),
        'feature1': np.arange(20).astype(float),
        'delay_minutes': (np.arange(20) * 0.5) + np.random.RandomState(0).randn(20) * 0.1
    })
    mb = ModelBuilder(df)
    # choose split after day 14 => first 15 rows train, last 5 test
    split_date = '2020-01-15'
    res = mb.perform_temporal_holdout(time_column='scheduled_time', split_date=split_date, target_column='delay_minutes', model_name='RandomForest')
    assert isinstance(res, dict)
    assert res['train_size'] >= 1
    assert res['test_size'] >= 1
    # metrics keys present
    assert 'test_r2' in res and 'test_mae' in res and 'test_rmse' in res
'''

with open('tests/test_temporal_holdout.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Wrote tests/test_temporal_holdout.py')
