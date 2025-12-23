"""Rebuild generated outputs by cleaning then running export_data_view.py

Usage:
    python scripts/rebuild_outputs.py
"""
import subprocess
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable

print('Cleaning existing outputs...')
subprocess.check_call([PY, str(ROOT / 'scripts' / 'clean_outputs.py')])
print('Re-running export_data_view to regenerate outputs...')
subprocess.check_call([PY, str(ROOT / 'scripts' / 'export_data_view.py')])

# After data is regenerated, train a model, save artifacts, and generate reports
print('Training models and generating reports...')
import pandas as pd
import matplotlib.pyplot as plt
import joblib
import argparse
# ensure src is on path for local imports
import sys
sys.path.insert(0, str(ROOT / 'src'))
from transport_analysis.model_builder import ModelBuilder
from transport_analysis.explainer import ModelExplainer
from transport_analysis.feature_engineer import FeatureEngineer

parser = argparse.ArgumentParser(description='Rebuild outputs and optionally force winsorized features for modeling')
parser.add_argument('--no-winsor', dest='winsorize', action='store_false', help='Do not apply winsorization to engineered features (default: enabled)')
args = parser.parse_args()

engineered_path = ROOT / 'results' / 'engineered_transport_data.csv'
df = None
if engineered_path.exists():
    df = pd.read_csv(engineered_path)

# If winsorization is requested (default) ensure the dataframe used for modeling
# contains winsorized columns. If not present, recompute engineered features
# from the cleaned dataset with winsorization enabled.
if args.winsorize:
    need_recompute = True
    if df is not None:
        if 'passenger_count_winsor' in df.columns and 'delay_minutes_winsor' in df.columns:
            need_recompute = False
    if need_recompute:
        # Load cleaned data (export_data_view.py already regenerated it above)
        cleaned_path = ROOT / 'results' / 'cleaned_transport_data.csv'
        if cleaned_path.exists():
            cleaned_df = pd.read_csv(cleaned_path)
        elif df is not None:
            # fallback to engineered df (best effort)
            cleaned_df = df.copy()
        else:
            cleaned_df = pd.DataFrame()
        fe = FeatureEngineer(cleaned_df)
        df = fe.run_full_feature_engineering(winsorize=True)
# if winsorization disabled and we didn't load engineered file, try to load cleaned
if df is None:
    cleaned_path = ROOT / 'results' / 'cleaned_transport_data.csv'
    if cleaned_path.exists():
        df = pd.read_csv(cleaned_path)

# proceed to build models
mb = ModelBuilder(df)
mb.run_all_models()
comp = mb.get_model_comparison()
# save a simple performance bar chart
if not comp.empty:
    comp_plot = (ROOT / 'results' / 'model_performance_comparison.png')
    try:
        models = comp['Model'].tolist()
        scores = comp['Test R²'].tolist()
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(models, scores)
        ax.set_ylabel('Test R²')
        ax.set_ylim(min(-1, min(scores) - 0.1), max(1, max(scores) + 0.1))
        plt.xticks(rotation=45)
        plt.tight_layout()
        fig.savefig(comp_plot, dpi=100, bbox_inches='tight')
        plt.close(fig)
        print(f'Saved performance plot to: {comp_plot}')
    except Exception as e:
        print('Could not create performance plot:', e)
    # save comparison CSV
    try:
        comp_csv = ROOT / 'results' / 'model_performance_comparison.csv'
        comp.to_csv(comp_csv, index=False)
        print(f'Saved performance comparison CSV to: {comp_csv}')
    except Exception as e:
        print('Could not save comparison CSV:', e)

    # save best model
    best_name, best_model = mb.get_best_model()
    if best_model is not None:
        model_path = ROOT / 'results' / f'model_{best_name}.pkl'
        joblib.dump(best_model, model_path)
        print(f'Saved model to: {model_path}')

        # Also save all trained models for reproducibility (ensures model_RandomForest.pkl exists)
        try:
            for name, model in mb.models.items():
                try:
                    path = ROOT / 'results' / f'model_{name}.pkl'
                    joblib.dump(model, path)
                    print(f'Saved model to: {path}')
                except Exception:
                    print(f'Could not save model {name}')
        except Exception:
            pass

        # create explainability report (including CV summaries)
        try:
            # Create multi-model explainability report for all trained models
            from transport_analysis.explainer import create_multi_model_explainability_report, ModelExplainer
            feature_names = mb.prepare_data()[-1]
            # Prepare CV summaries for each model (use full X,y)
            X_train, X_test, y_train, y_test, fnames = mb._prepared_data
            X_all = pd.concat([X_train, X_test], axis=0)
            y_all = pd.concat([y_train, y_test], axis=0)
            cv_results = {}
            for mname in mb.models.keys():
                try:
                    cv = mb.perform_cross_validation(X_all, y_all, mname, cv=5)
                    cv_results[mname] = cv
                except Exception:
                    cv_results[mname] = {}

            report_path = ROOT / 'results' / 'model_explainability_report.html'
            create_multi_model_explainability_report(mb.models, df[feature_names], feature_names=feature_names, output_path=str(report_path), cv_results=cv_results)
            print(f'Multi-model explainability report saved to: {report_path}')

            # compute time-series CV per model and save per-model fold plots
            try:
                for mname in mb.models.keys():
                    try:
                        tscv_res = mb.perform_time_series_cv(X_all, y_all, mname, n_splits=5)
                        # save a simple line plot of fold scores
                        import matplotlib.pyplot as plt
                        scores = tscv_res.get('cv_scores', [])
                        if scores:
                            fig, ax = plt.subplots(figsize=(6, 3))
                            ax.plot(range(1, len(scores) + 1), scores, marker='o')
                            ax.set_xlabel('Fold')
                            ax.set_ylabel('R²')
                            ax.set_title(f'Time-series CV R²: {mname}')
                            ax.grid(True, linestyle='--', alpha=0.4)
                            outp = ROOT / 'results' / f'{mname}_tscv_plot.png'
                            plt.tight_layout()
                            fig.savefig(outp, dpi=100, bbox_inches='tight')
                            plt.close(fig)
                            print(f'Saved time-series CV plot to: {outp}')
                            # also add to cv_results for completeness
                            cv_results.setdefault(mname, {})['tscv_plot'] = str(outp)
                    except Exception:
                        pass
            except Exception:
                pass

            # generate full-sample SHAP per model (may be slow) and append images to report
            try:
                from transport_analysis.explainer import generate_full_shap_for_best_model
                shap_images_by_model = {}
                for mname in mb.models.keys():
                    try:
                        imgs = generate_full_shap_for_best_model(mb.models, df[feature_names], feature_names=feature_names, out_dir=str(ROOT / 'results'), best_model_name=mname)
                        if imgs:
                            shap_images_by_model[mname] = imgs
                    except Exception:
                        pass
                # append per-model SHAP and tscv images to the report HTML
                try:
                    with open(report_path, 'a', encoding='utf-8') as rf:
                        rf.write('<h2>Per-model time-series CV and full-sample SHAP</h2>')
                        for mname in mb.models.keys():
                            rf.write(f'<h3>{mname}</h3>')
                            # tscv plot
                            tscv_p = cv_results.get(mname, {}).get('tscv_plot') if cv_results.get(mname) else None
                            if not tscv_p:
                                # fallback to file if exists
                                candidate = ROOT / 'results' / f'{mname}_tscv_plot.png'
                                if candidate.exists():
                                    tscv_p = str(candidate.name)
                            if tscv_p:
                                rf.write(f'<p>Time-series CV:</p><img src="{Path(tscv_p).name}" style="max-width:600px;"></img>')
                            # shap images
                            imgs = shap_images_by_model.get(mname, [])
                            for im in imgs:
                                rf.write(f'<p>SHAP plot:</p><img src="{Path(im).name}" style="max-width:700px;"></img>')
                except Exception:
                    pass
            except Exception:
                pass
        except Exception as e:
            print('Failed to create explainability report:', e)

        # also save a shap or fallback summary plot
        try:
            # try shap summary first
            # We'll still try to save a combined SHAP summary plot for the best model
            from transport_analysis.explainer import ModelExplainer
            best_name2, best_model2 = mb.get_best_model()
            if best_model2 is not None:
                best_expl = ModelExplainer(best_model2, feature_names=feature_names)
                plt_obj = best_expl.plot_shap_summary(df[feature_names])
                shap_plot = ROOT / 'results' / 'shap_summary_plot.png'
                try:
                    plt_obj.savefig(shap_plot, dpi=100, bbox_inches='tight')
                    plt.close()
                    print(f'Saved SHAP summary plot to: {shap_plot}')
                except Exception:
                    # fallback to df from get_feature_impact_summary
                    df_shap = best_expl.get_feature_impact_summary(df[feature_names])
                    fig, ax = plt.subplots(figsize=(6, 4))
                    ax.barh(df_shap['feature'].head(10)[::-1], df_shap['mean_abs_shap'].head(10)[::-1])
                    plt.tight_layout()
                    fig.savefig(shap_plot, dpi=100, bbox_inches='tight')
                    plt.close(fig)
                    print(f'Saved fallback SHAP summary plot to: {shap_plot}')
        except Exception as e:
            print('Could not save SHAP plot:', e)

print('Rebuild complete.')