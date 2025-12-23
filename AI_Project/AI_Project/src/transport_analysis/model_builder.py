import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split, cross_val_score, TimeSeriesSplit
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error


class ModelBuilder:
    def __init__(self, engineered_df: pd.DataFrame):
        self.df = engineered_df.copy()
        self.models = {}
        self.feature_importance = {}
        self._prepared_data = None  # cached (X_train, X_test, y_train, y_test, feature_names)

    def prepare_data(self, target_column='delay_minutes', test_size=0.2, random_state=42):
        # Keep DataFrames to preserve column names for downstream uses
        X = self.df.drop(columns=[target_column], errors='ignore').select_dtypes(include=[np.number])
        y = self.df[target_column] if target_column in self.df.columns else pd.Series(np.zeros(len(X)))
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)
        feature_names = X.columns.tolist()
        self._prepared_data = (X_train, X_test, y_train, y_test, feature_names)
        return X_train, X_test, y_train, y_test, feature_names

    def run_all_models(self, test_size=0.2, random_state=42):
        # Train a simple RandomForest and record metrics and feature importances
        X_train, X_test, y_train, y_test, feature_names = self.prepare_data(test_size=test_size, random_state=random_state)
        rf = RandomForestRegressor(n_estimators=50, random_state=random_state)
        rf.fit(X_train, y_train)
        self.models['RandomForest'] = rf

        # record feature importance
        importances = getattr(rf, 'feature_importances_', None)
        if importances is not None:
            self.feature_importance['RandomForest'] = dict(zip(feature_names, importances.tolist()))

        # compute test metrics and store
        try:
            preds = rf.predict(X_test)
            r2 = float(r2_score(y_test, preds))
            mae = float(mean_absolute_error(y_test, preds))
            rmse = float(mean_squared_error(y_test, preds, squared=False))
        except Exception:
            r2, mae, rmse = 0.0, 0.0, 0.0

        # store metrics for quick access
        if not hasattr(self, 'model_metrics'):
            self.model_metrics = {}
        self.model_metrics['RandomForest'] = {'test_r2': r2, 'test_mae': mae, 'test_rmse': rmse}
        # Also train a linear regression baseline
        try:
            lr = LinearRegression()
            lr.fit(X_train, y_train)
            self.models['LinearRegression'] = lr
            # record linear coefficients as feature importance proxy
            try:
                coefs = getattr(lr, 'coef_', None)
                if coefs is not None:
                    self.feature_importance['LinearRegression'] = dict(zip(feature_names, coefs.tolist()))
            except Exception:
                pass

            preds_lr = lr.predict(X_test)
            r2_lr = float(r2_score(y_test, preds_lr))
            mae_lr = float(mean_absolute_error(y_test, preds_lr))
            rmse_lr = float(mean_squared_error(y_test, preds_lr, squared=False))
        except Exception:
            r2_lr, mae_lr, rmse_lr = 0.0, 0.0, 0.0

        self.model_metrics['LinearRegression'] = {'test_r2': r2_lr, 'test_mae': mae_lr, 'test_rmse': rmse_lr}

        return {
            'RandomForest': {'model': rf, 'test_r2': r2, 'test_mae': mae, 'test_rmse': rmse},
            'LinearRegression': {'model': self.models.get('LinearRegression'), 'test_r2': r2_lr, 'test_mae': mae_lr, 'test_rmse': rmse_lr}
        }

    def perform_time_series_cv(self, X, y, model_name, n_splits=5):
        """
        Perform time-series cross validation using TimeSeriesSplit and return fold scores.
        """
        model = self.models.get(model_name)
        if model is None:
            return {'cv_scores': [], 'cv_mean_r2': 0.0, 'cv_std_r2': 0.0}
        tscv = TimeSeriesSplit(n_splits=n_splits)
        scores = []
        for train_idx, test_idx in tscv.split(X):
            try:
                X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
                y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
                # clone model to avoid refit side-effects
                from sklearn.base import clone
                m = clone(model)
                m.fit(X_train, y_train)
                preds = m.predict(X_test)
                scores.append(float(r2_score(y_test, preds)))
            except Exception:
                scores.append(0.0)
        import numpy as _np
        arr = _np.array(scores)
        return {'cv_scores': arr.tolist(), 'cv_mean_r2': float(arr.mean()), 'cv_std_r2': float(arr.std())}

    def plot_cv_comparison(self, cv_results: dict, out_path: str = None):
        """
        Create a boxplot comparing CV scores across models. `cv_results` should be a dict name->cv_dict.
        """
        import matplotlib.pyplot as plt
        labels = []
        data = []
        for name, cv in cv_results.items():
            scores = cv.get('cv_scores') or []
            if scores:
                labels.append(name)
                data.append(scores)
        if not data:
            return None
        plt.figure(figsize=(8, 6))
        plt.boxplot(data, labels=labels, showmeans=True)
        plt.ylabel('R²')
        plt.title('Cross-validation R² comparison')
        try:
            plt.tight_layout()
        except Exception:
            pass
        if out_path:
            plt.savefig(out_path, bbox_inches='tight')
            try:
                plt.close()
            except Exception:
                pass
        return out_path

    def get_model_comparison(self):
        # Return a DataFrame with model-level test metrics (if available)
        rows = []
        for name in self.models.keys():
            metrics = getattr(self, 'model_metrics', {}).get(name, {})
            rows.append({
                'Model': name,
                'Test R²': metrics.get('test_r2', 0.0),
                'Test MAE': metrics.get('test_mae', 0.0),
                'Test RMSE': metrics.get('test_rmse', 0.0)
            })
        return pd.DataFrame(rows)

    def get_best_model(self):
        # Return best model by Test R² if available
        if not self.models:
            return None, None
        best_name = None
        best_r2 = -float('inf')
        for name, model in self.models.items():
            r2 = getattr(self, 'model_metrics', {}).get(name, {}).get('test_r2', None)
            if r2 is None:
                continue
            if r2 > best_r2:
                best_r2 = r2
                best_name = name
        if best_name:
            return best_name, self.models[best_name]
        # fallback
        if 'RandomForest' in self.models:
            return 'RandomForest', self.models['RandomForest']
        return None, None

    def perform_temporal_holdout(self, time_column, split_date, target_column='delay_minutes', model_name='RandomForest'):
        """
        Train on data where `time_column` <= `split_date` and evaluate on data > `split_date`.
        `split_date` may be a string parsable by pandas or a datetime-like object.
        Returns metrics dict: {'train_size', 'test_size', 'test_r2', 'test_mae', 'test_rmse'}
        """
        import pandas as _pd
        if time_column not in self.df.columns:
            raise ValueError(f"Time column '{time_column}' not found in dataframe")
        df = self.df.copy()
        # ensure datetime
        try:
            df[time_column] = _pd.to_datetime(df[time_column], errors='coerce')
        except Exception:
            df[time_column] = _pd.to_datetime(df[time_column], errors='coerce')
        # parse split_date
        try:
            split_dt = _pd.to_datetime(split_date)
        except Exception:
            split_dt = split_date

        train_df = df[df[time_column] <= split_dt]
        test_df = df[df[time_column] > split_dt]
        if train_df.empty or test_df.empty:
            return {'train_size': len(train_df), 'test_size': len(test_df), 'test_r2': None, 'test_mae': None, 'test_rmse': None}

        # select numeric features and drop target
        X_train = train_df.select_dtypes(include=[float, int]).drop(columns=[target_column], errors='ignore')
        y_train = train_df[target_column] if target_column in train_df.columns else _pd.Series([0]*len(X_train))
        X_test = test_df.select_dtypes(include=[float, int]).drop(columns=[target_column], errors='ignore')
        y_test = test_df[target_column] if target_column in test_df.columns else _pd.Series([0]*len(X_test))

        # choose model
        if model_name not in self.models:
            # try to initialize default model
            if model_name == 'RandomForest':
                from sklearn.ensemble import RandomForestRegressor
                model = RandomForestRegressor(n_estimators=50)
            else:
                from sklearn.linear_model import LinearRegression
                model = LinearRegression()
        else:
            model = self.models[model_name]

        # fit and evaluate
        try:
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            r2 = float(r2_score(y_test, preds))
            mae = float(mean_absolute_error(y_test, preds))
            rmse = float(mean_squared_error(y_test, preds, squared=False))
        except Exception:
            r2, mae, rmse = None, None, None

        return {'train_size': len(X_train), 'test_size': len(X_test), 'test_r2': r2, 'test_mae': mae, 'test_rmse': rmse}

    def save_model(self, model_name: str, path: str):
        """Save a trained model by name to a file using joblib."""
        import joblib
        model = self.models.get(model_name)
        if model is None:
            raise ValueError(f"Model '{model_name}' not found")
        joblib.dump(model, path)
        return path

    @staticmethod
    def load_model(path: str):
        """Load a model saved with joblib from a file."""
        import joblib
        return joblib.load(path)

    def perform_cross_validation(self, X, y, model_name, cv=5):
        model = self.models.get(model_name)
        if model is None:
            return {'cv_scores': [], 'cv_mean_r2': 0.0, 'cv_std_r2': 0.0}
        # use R^2 as scoring
        scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
        return {'cv_scores': scores.tolist(), 'cv_mean_r2': float(scores.mean()), 'cv_std_r2': float(scores.std())}
