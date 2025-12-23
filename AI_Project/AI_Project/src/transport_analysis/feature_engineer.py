import pandas as pd
import numpy as np


class FeatureEngineer:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def run_full_feature_engineering(self, winsorize: bool = False, lower_q: float = 0.01, upper_q: float = 0.99):
        df = self.df
        # Example features: passenger_count (ensure numeric), hour of day if available
        if 'passenger_count' in df.columns:
            df['passenger_count'] = pd.to_numeric(df['passenger_count'], errors='coerce').fillna(0)

        # scheduled_time -> hour
        if 'scheduled_time' in df.columns:
            try:
                dt = pd.to_datetime(df['scheduled_time'], errors='coerce')
                df['scheduled_hour'] = dt.dt.hour.fillna(0).astype(int)
            except Exception:
                df['scheduled_hour'] = 0

        # time of day bucket
        if 'scheduled_hour' in df.columns:
            def tod(h):
                if 6 <= h < 12:
                    return 'morning'
                if 12 <= h < 17:
                    return 'afternoon'
                if 17 <= h < 22:
                    return 'evening'
                return 'night'

            df['time_of_day'] = df['scheduled_hour'].apply(tod)

        # Day type: weekday vs weekend and is_weekend flag
        if 'scheduled_time' in df.columns:
            try:
                dt = pd.to_datetime(df['scheduled_time'], errors='coerce')
                df['day_of_week'] = dt.dt.weekday  # 0=Mon..6=Sun
                df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
                df['day_type'] = df['is_weekend'].map({0: 'weekday', 1: 'weekend'})
            except Exception:
                df['day_of_week'] = 0
                df['is_weekend'] = 0
                df['day_type'] = 'weekday'

        # Weather severity index (light=0, moderate=1, heavy=2) + categorical label
        if 'weather' in df.columns:
            def severity_label(w):
                if not isinstance(w, str):
                    return ('light', 0)
                s = w.strip().lower()
                if any(x in s for x in ['heavy', 'storm', 'rainy', 'thunder']):
                    return ('heavy', 2)
                if any(x in s for x in ['moderate', 'moderate rain', 'showers']):
                    return ('moderate', 1)
                # treat cloudy/overcast as light-to-moderate
                if any(x in s for x in ['cloud', 'clody', 'overcast']):
                    return ('moderate', 1)
                # sunny, clear, fair => light
                if any(x in s for x in ['sun', 'sunny', 'clear', 'fair']):
                    return ('light', 0)
                # default fallback
                return ('light', 0)

            sev = df['weather'].apply(lambda w: severity_label(w))
            df['weather_severity_cat'] = sev.apply(lambda t: t[0])
            df['weather_severity'] = sev.apply(lambda t: t[1])

        # Route frequency: count occurrences of each route_id (simple proxy for route frequency)
        if 'route_id' in df.columns:
            try:
                df['route_id_clean'] = df['route_id'].astype(str).str.strip()
                df['route_frequency'] = df.groupby('route_id_clean')['route_id_clean'].transform('count')
                # normalized frequency (per-dataset scale)
                maxf = df['route_frequency'].max() if df['route_frequency'].max() > 0 else 1
                df['route_frequency_norm'] = df['route_frequency'] / maxf
            except Exception:
                df['route_frequency'] = 0
                df['route_frequency_norm'] = 0

        # One-hot a small set of categorical columns for modelling but keep originals
        cat_cols = [c for c in ['weather', 'weather_severity_cat', 'route_id', 'time_of_day', 'day_type'] if c in df.columns]
        if cat_cols:
            dummies = pd.get_dummies(df[cat_cols].astype(str), dummy_na=False)
            df = pd.concat([df, dummies], axis=1)

        # Optional winsorization for numeric stability (applies to passenger_count and delay_minutes)
        if winsorize:
            nums = [c for c in ['passenger_count', 'delay_minutes'] if c in df.columns]
            for c in nums:
                try:
                    low = df[c].quantile(lower_q)
                    high = df[c].quantile(upper_q)
                    df[c + '_orig'] = df[c]
                    df[c + '_winsor'] = df[c].clip(lower=low, upper=high)
                except Exception:
                    df[c + '_orig'] = df.get(c)
                    df[c + '_winsor'] = df.get(c)

        self.df = df
        return df

    def get_feature_list(self):
        # Return numeric columns as features excluding target
        features = [c for c in self.df.select_dtypes(include=[np.number]).columns if c != 'delay_minutes']
        return features
