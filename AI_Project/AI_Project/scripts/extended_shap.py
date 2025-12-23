"""Generate extended SHAP plots (full-sample or larger sample) for all trained models.
Saves images to results/ and prints created file paths.
"""
import os
import sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pandas as pd
from transport_analysis.model_builder import ModelBuilder
from transport_analysis.feature_engineer import FeatureEngineer
from transport_analysis.explainer import generate_full_shap_for_best_model

DATA = os.path.join(ROOT, 'results', 'engineered_transport_data.csv')
OUT_DIR = os.path.join(ROOT, 'results')

if __name__ == '__main__':
    if not os.path.exists(DATA):
        print('Engineered data not found, running rebuild_outputs.py first...')
        import subprocess
        subprocess.check_call([sys.executable, os.path.join(ROOT, 'scripts', 'rebuild_outputs.py')])

    df = pd.read_csv(DATA)
    # pick numeric feature columns as feature_names
    X = df.select_dtypes(include=[float, int]).copy()
    # remove target if present
    if 'delay_minutes' in X.columns:
        X = X.drop(columns=['delay_minutes'])

    mb = ModelBuilder(df)
    mb.run_all_models()

    feature_names = X.columns.tolist()
    generated = []
    for mname in mb.models.keys():
        try:
            imgs = generate_full_shap_for_best_model(mb.models, X, feature_names=feature_names, out_dir=OUT_DIR, best_model_name=mname)
            if imgs:
                for im in imgs:
                    if os.path.exists(im):
                        generated.append(im)
        except Exception as e:
            print('Failed for', mname, e)

    if generated:
        print('Generated SHAP images:')
        for g in generated:
            print(' -', g)
    else:
        print('No SHAP images generated.')
