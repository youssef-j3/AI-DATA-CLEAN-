import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from .utils import align_shap_with_features

try:
    import shap
except Exception:
    shap = None


class ModelExplainer:
    def __init__(self, model, feature_names=None):
        self.model = model
        self.feature_names = feature_names
        self.shap_values = None

    def calculate_shap_values(self, X, sample_size=None):
        X_arr = np.asarray(X)
        if shap is None:
            # shap not available, return zeros with shape (n_samples, n_features)
            self.shap_values = np.zeros(X_arr.shape)
            return self.shap_values

        # use TreeExplainer where possible
        try:
            expl = shap.Explainer(self.model)
            if sample_size is not None and sample_size < X_arr.shape[0]:
                Xs = X_arr[np.random.choice(X_arr.shape[0], sample_size, replace=False)]
            else:
                Xs = X_arr
            sv = expl(Xs)
            # shap.Explanation objects can be converted
            self.shap_values = sv.values
        except Exception:
            # fallback to TreeExplainer from shap
            try:
                expl = shap.TreeExplainer(self.model)
                sv = expl.shap_values(X_arr if sample_size is None else X_arr[:sample_size])
                self.shap_values = sv
            except Exception:
                self.shap_values = np.zeros(X_arr.shape)

        # align shapes
        self.shap_values = align_shap_with_features(self.shap_values, X_arr)
        # normalize to 2D array (n_samples, n_features) when possible
        try:
            arr = np.asarray(self.shap_values)
            if arr.ndim == 3:
                arr = arr.mean(axis=0)
            # ensure it's 2D
            if arr.ndim == 2:
                self.shap_values = arr
        except Exception:
            # fallback to zeros of right shape
            self.shap_values = np.zeros(X_arr.shape)
        return self.shap_values

    def get_feature_impact_summary(self, X):
        sv = self.shap_values if self.shap_values is not None else self.calculate_shap_values(X)
        # if list or class-based return mean across classes
        arr = np.asarray(sv)
        if arr.ndim == 3:
            # (n_classes, n_samples, n_features)
            arr = arr.mean(axis=0)
        if isinstance(sv, list):
            arr = np.asarray(sv).mean(axis=0)
        mean_abs = np.abs(arr).mean(axis=0)
        features = self.feature_names if self.feature_names is not None else [f'f{i}' for i in range(mean_abs.shape[0])]
        df = pd.DataFrame({'feature': features, 'mean_abs_shap': mean_abs})
        df = df.sort_values('mean_abs_shap', ascending=False).reset_index(drop=True)
        return df

    def plot_shap_summary(self, X, max_display=10):
        if shap is None:
            # simple bar of mean_abs_shap
            df = self.get_feature_impact_summary(X).head(max_display)
            plt.figure(figsize=(8, 6))
            plt.barh(df['feature'][::-1], df['mean_abs_shap'][::-1])
            try:
                plt.tight_layout()
            except Exception:
                pass
            return plt

        if self.shap_values is None:
            self.calculate_shap_values(X)
        else:
            self.shap_values = align_shap_with_features(self.shap_values, X)

        plt.figure(figsize=(12, 8))
        try:
            shap.summary_plot(self.shap_values, X, feature_names=self.feature_names, max_display=max_display, show=False)
        except Exception:
            # fallback to mean-abs bar chart
            df = self.get_feature_impact_summary(X).head(max_display)
            plt.clf()
            plt.barh(df['feature'][::-1], df['mean_abs_shap'][::-1])
        try:
            plt.tight_layout()
        except Exception:
            pass
        return plt

    def plot_feature_importance(self, importance_dict, top_n=10):
        items = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)[:top_n]
        feats, imps = zip(*items) if items else ([], [])
        plt.figure(figsize=(8, 6))
        plt.barh(list(feats)[::-1], list(imps)[::-1])
        try:
            plt.tight_layout()
        except Exception:
            pass
        return plt

    def plot_shap_dependence(self, X, feature_idx):
        if shap is None:
            raise RuntimeError('shap not installed')
        try:
            shap.dependence_plot(feature_idx, self.shap_values, X, feature_names=self.feature_names, show=False)
            return plt
        except Exception as e:
            raise

    def create_explainability_report(self, X, output_path='model_explainability_report.html'):
        # Minimal HTML report with feature table
        df = self.get_feature_impact_summary(X)
        html = df.head(20).to_html(index=False)
        with open(output_path, 'w') as f:
            f.write('<h1>Model Explainability Report</h1>')
            f.write(html)
        return output_path


def create_multi_model_explainability_report(models: dict, X, feature_names=None, output_path='model_explainability_report.html', cv_results: dict = None):
    """
    Create an HTML report comparing feature importance / SHAP across multiple models.
    `models` should be a dict of name->model objects. `X` is a DataFrame of features.
    """
    import os
    out_dir = os.path.dirname(output_path) or '.'
    os.makedirs(out_dir, exist_ok=True)
    # If CV results are provided, create a combined CV comparison boxplot
    cv_plot_path = None
    try:
        if cv_results:
            # collect scores per model for boxplot
            scores_list = []
            labels = []
            for name in models.keys():
                cv = cv_results.get(name, {})
                scores = cv.get('cv_scores') if isinstance(cv, dict) else None
                if scores:
                    scores_list.append(scores)
                    labels.append(name)
            if scores_list:
                cv_plot_path = os.path.join(out_dir, 'cv_comparison_boxplot.png')
                plt.figure(figsize=(8, 6))
                plt.boxplot(scores_list, labels=labels, showmeans=True)
                plt.ylabel('R²')
                plt.title('Cross-validation R² comparison')
                try:
                    plt.tight_layout()
                except Exception:
                    pass
                plt.savefig(cv_plot_path, bbox_inches='tight')
                try:
                    plt.close()
                except Exception:
                    pass
    except Exception:
        cv_plot_path = None
    sections = []
    # if we created a CV comparison plot, include it at the top
    if cv_plot_path:
        sections.append(f'<h2>Cross-validation Comparison</h2><img src="{os.path.basename(cv_plot_path)}" alt="CV comparison" style="max-width:700px;">')
    for name, model in models.items():
        try:
            expl = ModelExplainer(model, feature_names=feature_names)
            # compute shap if possible (sample to limit runtime)
            try:
                expl.calculate_shap_values(X, sample_size=min(200, len(X)))
            except Exception:
                pass
            # feature impact table
            df_imp = expl.get_feature_impact_summary(X).head(20)
            table_html = df_imp.to_html(index=False)

            # Try to get model-native importances as fallback
            imp_dict = {}
            try:
                if hasattr(model, 'feature_importances_'):
                    imp = getattr(model, 'feature_importances_')
                    imp_dict = dict(zip(feature_names, imp.tolist()))
                elif hasattr(model, 'coef_'):
                    coefs = getattr(model, 'coef_')
                    # handle multi-dim coeff arrays
                    if getattr(coefs, 'ndim', 1) == 1:
                        imp_dict = dict(zip(feature_names, coefs.tolist()))
                    else:
                        imp_dict = dict(zip(feature_names, np.abs(coefs).mean(axis=0).tolist()))
            except Exception:
                imp_dict = {}

            # save a quick bar plot for model importances (either shap mean-abs or model imp)
            plot_path = os.path.join(out_dir, f'{name}_feature_importance.png')
            try:
                if not imp_dict:
                    # use shap summary table
                    fig = expl.plot_shap_summary(X, max_display=10)
                    fig.savefig(plot_path, bbox_inches='tight')
                    try:
                        plt.close(fig)
                    except Exception:
                        pass
                else:
                    fig = expl.plot_feature_importance(imp_dict, top_n=10)
                    fig.savefig(plot_path, bbox_inches='tight')
                    try:
                        plt.close(fig)
                    except Exception:
                        pass
            except Exception:
                plot_path = None

            section_html = f'<h2>{name}</h2>'
            # Add CV summary table if available
            if cv_results and name in cv_results:
                cv = cv_results[name]
                # show mean and std of R2 and raw scores
                cv_html = '<h3>Cross-validation (R²) summary</h3>'
                try:
                    mean_r2 = cv.get('cv_mean_r2')
                    std_r2 = cv.get('cv_std_r2')
                    scores = cv.get('cv_scores', [])
                    cv_html += f'<p>Mean R²: {mean_r2:.4f} &nbsp; Std: {std_r2:.4f}</p>'
                    if scores:
                        scores_table = '<table><tr>' + ''.join(f'<th>fold{i+1}</th>' for i in range(len(scores))) + '</tr>'
                        scores_table += '<tr>' + ''.join(f'<td>{s:.4f}</td>' for s in scores) + '</tr></table>'
                        cv_html += scores_table
                except Exception:
                    cv_html += '<p>CV summary not available</p>'
                section_html += cv_html
            if plot_path:
                section_html += f'<img src="{os.path.basename(plot_path)}" alt="{name} importance" style="max-width:600px;">'
            section_html += table_html
            sections.append(section_html)
        except Exception as e:
            sections.append(f'<h2>{name}</h2><p>Could not explain model: {e}</p>')

    # assemble HTML
    html = '<html><head><meta charset="utf-8"><title>Multi-model Explainability</title></head><body>'
    html += '<h1>Multi-model Explainability Report</h1>'
    for s in sections:
        html += s
        html += '<hr/>'
    html += '</body></html>'

    # write report and copy images references relative to output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    # attempt to create a full-sample SHAP for best model and include in report directory
    try:
        best_name = None
        # prefer model with highest cv mean r2 if cv_results provided
        if cv_results:
            try:
                best_name = max(cv_results.keys(), key=lambda k: cv_results[k].get('cv_mean_r2', -1))
            except Exception:
                best_name = None
        if not best_name:
            if 'RandomForest' in models:
                best_name = 'RandomForest'
            else:
                best_name = next(iter(models.keys()), None)
        if best_name:
            shap_files = generate_full_shap_for_best_model(models, X, feature_names=feature_names, out_dir=out_dir, best_model_name=best_name)
            # update report to reference generated files (append links)
            if shap_files:
                with open(output_path, 'a', encoding='utf-8') as f:
                    f.write('<h2>Full-sample SHAP for best model</h2>')
                    for p in shap_files:
                        f.write(f'<img src="{os.path.basename(p)}" style="max-width:700px;"></img>')
    except Exception:
        pass

    return output_path


def generate_full_shap_for_best_model(models: dict, X, feature_names=None, out_dir='.', best_model_name=None):
    """Generate full-sample SHAP summary and dependence plots for the best model.
    Saves files to out_dir and returns list of generated file paths.
    """
    import os
    os.makedirs(out_dir, exist_ok=True)
    # choose best model: prefer provided name, else RandomForest, else first
    model = None
    name = best_model_name
    if name and name in models:
        model = models[name]
    else:
        if 'RandomForest' in models:
            name = 'RandomForest'
            model = models[name]
        else:
            # pick first available
            try:
                name = next(iter(models.keys()))
                model = models[name]
            except StopIteration:
                return []

    if shap is None:
        return []

    expl = ModelExplainer(model, feature_names=feature_names)
    # compute full-sample shap (may be slow)
    try:
        expl.calculate_shap_values(X, sample_size=None)
    except Exception:
        # if fails, try sample fallback
        try:
            expl.calculate_shap_values(X, sample_size=min(500, len(X)))
        except Exception:
            return []

    generated = []
    try:
        # summary
        plt_obj = expl.plot_shap_summary(X, max_display=20)
        summary_path = os.path.join(out_dir, f'{name}_shap_summary_full.png')
        try:
            plt_obj.savefig(summary_path, bbox_inches='tight')
        except Exception:
            pass
        try:
            plt.close(plt_obj)
        except Exception:
            pass
        generated.append(summary_path)
        # top features for dependence plots
        try:
            df_imp = expl.get_feature_impact_summary(X)
            top_features = df_imp['feature'].head(3).tolist()
            for feat in top_features:
                if feat in feature_names:
                    idx = feature_names.index(feat)
                else:
                    continue
                # plot dependence
                try:
                    shap.dependence_plot(idx, expl.shap_values, X, feature_names=feature_names, show=False)
                    dep_path = os.path.join(out_dir, f'{name}_shap_dependence_{feat}.png')
                    plt.savefig(dep_path, bbox_inches='tight')
                    try:
                        plt.close()
                    except Exception:
                        pass
                    generated.append(dep_path)
                except Exception:
                    continue
        except Exception:
            pass
    except Exception:
        return generated
    return generated
