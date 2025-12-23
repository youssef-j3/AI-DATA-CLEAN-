import pandas as pd
import numpy as np
from transport_analysis.feature_engineer import FeatureEngineer


def test_feature_engineer_creates_expected_columns():
    data = {
        'scheduled_time': ['2025-12-22 08:00:00', '2025-12-21 15:30:00', '2025-12-20 20:00:00'],
        'weather': ['SUN', 'clody', 'Heavy Rain'],
        'route_id': ['R1', 'R1', 'R2'],
        'passenger_count': [10, 5, 2]
    }
    df = pd.DataFrame(data)

    fe = FeatureEngineer(df)
    out = fe.run_full_feature_engineering()

    # Check new columns exist
    for col in ['weather_severity', 'weather_severity_cat', 'route_frequency', 'route_frequency_norm', 'is_weekend', 'day_type', 'scheduled_hour', 'time_of_day']:
        assert col in out.columns

    # Weather severity categories
    assert out.loc[0, 'weather_severity_cat'] == 'light'
    assert out.loc[1, 'weather_severity_cat'] == 'moderate'
    assert out.loc[2, 'weather_severity_cat'] == 'heavy'

    # Numeric severity mapping
    assert int(out.loc[0, 'weather_severity']) == 0
    assert int(out.loc[1, 'weather_severity']) == 1
    assert int(out.loc[2, 'weather_severity']) == 2

    # Route frequency counts
    assert int(out.loc[0, 'route_frequency']) == 2
    assert int(out.loc[2, 'route_frequency']) == 1

    # Normalized frequency (max should be 1.0 for route R1)
    assert np.isclose(out.loc[0, 'route_frequency_norm'], 1.0)
    assert np.isclose(out.loc[2, 'route_frequency_norm'], 0.5)

    # Day type and is_weekend consistency
    # convert scheduled_time to weekday to check consistency
    dt = pd.to_datetime(out['scheduled_time'], errors='coerce')
    expected_is_weekend = dt.dt.weekday.isin([5, 6]).astype(int)
    assert out['is_weekend'].tolist() == expected_is_weekend.tolist()
    assert all(out.loc[out['is_weekend'] == 1, 'day_type'].eq('weekend'))
    assert all(out.loc[out['is_weekend'] == 0, 'day_type'].eq('weekday'))
