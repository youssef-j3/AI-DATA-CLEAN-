"""Clean generated outputs from results and root plots.

Usage:
    python scripts/clean_outputs.py
"""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
results = ROOT / 'results'
removed = []

# remove results directory contents
if results.exists() and results.is_dir():
    for p in results.iterdir():
        try:
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
            removed.append(str(p))
        except Exception as e:
            print(f"Could not remove {p}: {e}")

# common root outputs to remove
extras = [
    ROOT / 'model_explainability_report.html',
    ROOT / 'feature_importance_plot.png',
    ROOT / 'model_performance_comparison.png',
    ROOT / 'shap_summary_plot.png'
]
for p in extras:
    if p.exists():
        try:
            p.unlink()
            removed.append(str(p))
        except Exception as e:
            print(f"Could not remove {p}: {e}")

# remove eda_plots images
eda_dir = ROOT / 'eda_plots'
if eda_dir.exists():
    for p in eda_dir.glob('*.png'):
        try:
            p.unlink()
            removed.append(str(p))
        except Exception as e:
            print(f"Could not remove {p}: {e}")

print("Removed the following generated files:")
for r in removed:
    print(' -', r)

if not removed:
    print('No generated files found to remove.')