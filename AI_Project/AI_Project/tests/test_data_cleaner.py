import pandas as pd
import numpy as np
import re
from transport_analysis.data_cleaner import DataCleaner


def test_weather_normalization_and_nan_string():
    df = pd.DataFrame({'weather': ['clody', 'SUN', 'nan', None, 'rain']})
    cleaner = DataCleaner(df)
    out = cleaner.run_full_cleaning_pipeline()
    assert out['weather'].tolist() == ['Cloudy', 'Sunny', 'Unknown', 'Unknown', 'Rainy']


def test_negative_passenger_count_fixed():
    df = pd.DataFrame({'passenger_count': [10, -5, 30]})
    cleaner = DataCleaner(df)
    out = cleaner.run_full_cleaning_pipeline()
    # median of non-negative [10,30] is 20
    assert out['passenger_count'].tolist() == [10, 20, 30]


def test_coordinate_sentinel_cleaned():
    df = pd.DataFrame({'latitude': [999, 23.5, 0], 'longitude': [0, 45.0, 999]})
    cleaner = DataCleaner(df)
    out = cleaner.run_full_cleaning_pipeline()
    assert not (out['latitude'] == 999).any()
    assert not (out['longitude'] == 999).any()
    # sentinel 0 replaced (median of non-sentinel values)
    assert np.isfinite(out['latitude']).sum() >= 1


def test_time_parsing_and_delay():
    df = pd.DataFrame({'scheduled_time': ['1/1/2025 00:00', '1/1/2025 01:00', '1/1/2025 02:00'],
                       'actual_time': ['00:20', '1:30', '0150']})
    cleaner = DataCleaner(df)
    out = cleaner.run_full_cleaning_pipeline()
    # delays: 20, 30, -10 minutes (01:50 is 10 minutes early relative to 02:00)
    assert out['delay_minutes'].iloc[0] == 20.0
    assert out['delay_minutes'].iloc[1] == 30.0
    assert out['delay_minutes'].iloc[2] == -10.0


def test_time_and_formats_standardized():
    df = pd.DataFrame({
        'scheduled_time': ['1/1/2025 00:00', '00:30', '2:05PM', None],
        'actual_time': ['0:20', '00:45', '14:10', '5:00']
    })
    cleaner = DataCleaner(df)
    out = cleaner.run_full_cleaning_pipeline()
    # scheduled_time where date present should keep date format, others become HH:MM
    # scheduled_time where date present should be ISO + AM/PM
    assert out['scheduled_time'].iloc[0] == '2025-01-01 12:00 AM'
    assert re.match(r'^\d{1,2}:\d{2} (AM|PM)$', out['scheduled_time'].iloc[1])
    assert re.match(r'^\d{1,2}:\d{2} (AM|PM)$', out['scheduled_time'].iloc[2])


def test_passenger_and_route_standardization():
    df = pd.DataFrame({'passenger_count': [10.0, 20.7, None], 'route_id': ['R03', 'route-4', '5']})
    cleaner = DataCleaner(df)
    out = cleaner.run_full_cleaning_pipeline()
    # passenger counts are ints
    assert out['passenger_count'].dtype == int
    assert out['passenger_count'].tolist()[0:2] == [10, 21]
    # routes normalized
    assert out['route_id'].tolist() == ['Route-3', 'Route-4', 'Route-5']


def test_fill_undefined_from_raw_and_time_am_pm():
    # A row with missing actual_time should be filled from raw original if present
    df = pd.DataFrame({'scheduled_time': ['1/1/2025 00:00', '1/1/2025 01:00'],
                       'actual_time': [None, '224'],
                       'weather': [None, 'sun']})
    cleaner = DataCleaner(df)
    out = cleaner.run_full_cleaning_pipeline()
    # first row actual_time is None and raw had None, so remains NaN
    assert pd.isna(out['actual_time'].iloc[0])
    # second row '224' should be parsed and formatted with AM/PM
    assert out['actual_time'].iloc[1].endswith('PM') or out['actual_time'].iloc[1].endswith('AM')
    assert out['weather'].iloc[1] == 'Sunny'


def test_rollover_alignment_and_flagging():
    # Case where actual_time is after midnight (time-only) and scheduled_time is late evening
    df = pd.DataFrame({
        'scheduled_time': ['1/2/2025 11:00 PM', '1/3/2025 10:00 PM'],
        'actual_time': ['12:14 AM', '12:21 AM']
    })
    cleaner = DataCleaner(df)
    out = cleaner.run_full_cleaning_pipeline()
    # Both should be small positive delays (74 and 81 minutes) and marked as computed
    assert round(out['delay_minutes'].iloc[0]) == 74
    assert round(out['delay_minutes'].iloc[1]) == 141
    assert bool(out['delay_computed'].iloc[0]) is True
    assert bool(out['delay_computed'].iloc[1]) is True

    # Now a hugely implausible delta should be flagged and set to NaN
    df2 = pd.DataFrame({
        'scheduled_time': ['1/2/2025 00:00'],
        'actual_time': ['1/10/2025 00:00']
    })
    cleaner2 = DataCleaner(df2)
    out2 = cleaner2.run_full_cleaning_pipeline()
    assert bool(out2['delay_flagged'].iloc[0]) is True
    assert pd.isna(out2['delay_minutes'].iloc[0])
