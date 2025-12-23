"""Export cleaned and engineered datasets to human-readable text files.

Usage:
    python scripts/export_data_view.py

Creates:
- results/cleaned_data_view.txt  (preview of cleaned data)
- results/engineered_data_view.txt  (preview of engineered data)
- results/cleaned_transport_data.csv (full cleaned CSV)
- results/engineered_transport_data.csv (full engineered CSV)
"""
from pathlib import Path
import sys
import os

# allow imports from project root
sys.path.append(str(Path(__file__).resolve().parents[1] / 'src'))

import pandas as pd
from transport_analysis.data_loader import DataLoader
from transport_analysis.data_cleaner import DataCleaner
from transport_analysis.feature_engineer import FeatureEngineer

# locate dataset (same logic as notebook)
project_root = Path(__file__).resolve().parents[1]
possible_paths = [project_root / 'dirty_transport_dataset.csv', Path('dirty_transport_dataset.csv')]
for p in possible_paths:
    if p.exists():
        data_path = str(p)
        break
else:
    raise FileNotFoundError('dirty_transport_dataset.csv not found in project root')

print(f"Using dataset: {data_path}")

loader = DataLoader(data_path)
raw = loader.load_data()

cleaner = DataCleaner(raw)
cleaned = cleaner.run_full_cleaning_pipeline()

engineer = FeatureEngineer(cleaned)
# Enable winsorization by default for exported engineered dataset so downstream
# scripts/rebuild_outputs.py and reports use stable numeric features
engineered = engineer.run_full_feature_engineering(winsorize=True)

# Ensure results dir
results_dir = project_root / 'results'
results_dir.mkdir(exist_ok=True)

# Save full CSVs
cleaned_csv = results_dir / 'cleaned_transport_data.csv'
engineered_csv = results_dir / 'engineered_transport_data.csv'
cleaned.to_csv(cleaned_csv, index=False)
engineered.to_csv(engineered_csv, index=False)

# Save human-readable previews (first 200 rows)
cleaned_txt = results_dir / 'cleaned_data_view.txt'
engineered_txt = results_dir / 'engineered_data_view.txt'

with cleaned_txt.open('w', encoding='utf-8') as f:
    f.write('CLEANED DATA PREVIEW\n')
    f.write('='*40 + '\n')
    f.write(f'Shape: {cleaned.shape}\n\n')
    f.write(cleaned.head(200).to_string())

with engineered_txt.open('w', encoding='utf-8') as f:
    f.write('ENGINEERED DATA PREVIEW\n')
    f.write('='*40 + '\n')
    f.write(f'Shape: {engineered.shape}\n\n')
    f.write(engineered.head(200).to_string())

print(f"Saved cleaned CSV to: {cleaned_csv}")
print(f"Saved engineered CSV to: {engineered_csv}")
print(f"Saved cleaned preview to: {cleaned_txt}")
print(f"Saved engineered preview to: {engineered_txt}")