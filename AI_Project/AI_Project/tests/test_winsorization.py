import pandas as pd
import numpy as np
from transport_analysis.feature_engineer import FeatureEngineer


def test_winsorization_clips_extremes():
    data = {
        'scheduled_time': ['2025-12-22 08:00:00', '2025-12-21 15:30:00', '2025-12-20 20:00:00', '2025-12-20 09:00:00'],
        'weather': ['sunny', 'cloudy', 'rain', 'sunny'],
        'route_id': ['R1', 'R1', 'R2', 'R3'],
        'passenger_count': [10, 5, 10000, -999],
        'delay_minutes': [5, 3, 10000, -500]
    }
    df = pd.DataFrame(data)
    fe = FeatureEngineer(df)
    out = fe.run_full_feature_engineering(winsorize=True, lower_q=0.01, upper_q=0.99)

    # winsor columns created
    assert 'passenger_count_winsor' in out.columns
    assert 'delay_minutes_winsor' in out.columns

    # Check that extreme values are within the 1%-99% quantile bounds
    pc = out['passenger_count_winsor']
    dm = out['delay_minutes_winsor']
    assert pc.max() <= out['passenger_count'].quantile(0.99)
    assert pc.min() >= out['passenger_count'].quantile(0.01)
    assert dm.max() <= out['delay_minutes'].quantile(0.99)
    assert dm.min() >= out['delay_minutes'].quantile(0.01)
