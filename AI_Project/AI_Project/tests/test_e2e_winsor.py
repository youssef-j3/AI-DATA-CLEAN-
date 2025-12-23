import subprocess
import sys
from pathlib import Path
import pandas as pd
import numpy as np


def test_export_produces_winsorized_engineered_csv(tmp_path, monkeypatch):
    # Run the export script to regenerate cleaned + engineered CSVs
    project_root = Path(__file__).resolve().parents[1]
    script = project_root / 'scripts' / 'export_data_view.py'
    # Execute the script using the current Python
    subprocess.check_call([sys.executable, str(script)])

    eng_path = project_root / 'results' / 'engineered_transport_data.csv'
    assert eng_path.exists()
    df = pd.read_csv(eng_path)

    # winsorized columns should exist
    for col in ['passenger_count_winsor', 'delay_minutes_winsor']:
        assert col in df.columns

    # Check a basic bounds property: winsorized values are within 1%-99% quantiles
    for base_col in ['passenger_count', 'delay_minutes']:
        if base_col in df.columns:
            low = df[base_col].quantile(0.01)
            high = df[base_col].quantile(0.99)
            winsor_col = base_col + '_winsor'
            if winsor_col in df.columns:
                assert df[winsor_col].dropna().ge(low - 1e-8).all()
                assert df[winsor_col].dropna().le(high + 1e-8).all()
