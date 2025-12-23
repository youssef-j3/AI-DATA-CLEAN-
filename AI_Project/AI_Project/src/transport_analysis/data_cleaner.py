import pandas as pd
import numpy as np
import unicodedata
from datetime import datetime
import re


class DataCleaner:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        # keep a copy of original raw data for possible fill-back
        self.raw_df = df.copy()
        self.cleaning_steps = []

    def run_full_cleaning_pipeline(self):
        # Basic cleaning that keeps things simple and reproducible
        df = self.df
        # Trim whitespace and normalize unicode for string columns
        for c in df.select_dtypes(include=['object']).columns:
            # Cast to str to avoid errors, then normalize and strip
            df[c] = (
                df[c]
                .astype(str)
                .apply(lambda s: unicodedata.normalize('NFKC', s).strip() if pd.notna(s) else s)
            )
            # Convert common string placeholders to real NaN
            df[c] = df[c].replace({'nan': np.nan, 'None': np.nan, 'none': np.nan, '': np.nan})

        # Try to create a numeric target 'delay_minutes' if missing
        if 'delay_minutes' not in df.columns:
            df['delay_minutes'] = 0.0
            self.cleaning_steps.append('created_delay_minutes_default_0')

        # Parse scheduled_time and actual_time into datetimes where possible
        def _parse_time(val):
            if pd.isna(val):
                return np.nan
            s = str(val).strip()
            # Try common formats
            fmts = [
                '%m/%d/%Y %H:%M', '%m/%d/%Y %I:%M%p', '%m/%d/%Y %I:%M %p',
                '%m/%d/%Y %H:%M:%S', '%H:%M', '%I:%M%p', '%I:%M %p'
            ]
            for f in fmts:
                try:
                    return datetime.strptime(s, f)
                except Exception:
                    continue
            # Try to extract digits if it's a plain number like '1245' -> HHMM
            m = re.match(r'^(\d{1,4})$', s)
            if m:
                t = m.group(1).zfill(4)
                try:
                    return datetime.strptime(t, '%H%M')
                except Exception:
                    return np.nan
            return np.nan

        if 'scheduled_time' in df.columns:
            df['_scheduled_dt'] = df['scheduled_time'].apply(_parse_time)
        if 'actual_time' in df.columns:
            df['_actual_dt'] = df['actual_time'].apply(_parse_time)

        # Compute delay_minutes if possible: actual - scheduled in minutes
        if '_scheduled_dt' in df.columns and '_actual_dt' in df.columns:
            def _compute_delay(row):
                s = row['_scheduled_dt']
                a = row['_actual_dt']
                if pd.isna(s) or pd.isna(a):
                    return np.nan
                try:
                    # Robust alignment for time-only datetimes (year==1900):
                    # If actual has no date (year==1900) but scheduled has a real date,
                    # consider both same-day and next-day alignments and pick the smallest
                    # absolute delta that is within a sensible window (12 hours).
                    if hasattr(a, 'year') and a.year == 1900 and hasattr(s, 'year') and s.year != 1900:
                        base = a.replace(year=s.year, month=s.month, day=s.day)
                        cand_same = base
                        cand_next = base + pd.Timedelta(days=1)
                        delta_same = (cand_same - s).total_seconds() / 60.0
                        delta_next = (cand_next - s).total_seconds() / 60.0
                        # choose the candidate with the smaller absolute delta, but prefer
                        # deltas within +/- 12 hours (720 minutes)
                        candidates = [(abs(delta_same), delta_same), (abs(delta_next), delta_next)]
                        candidates.sort(key=lambda x: x[0])
                        chosen = candidates[0][1]
                        if abs(chosen) <= 720:
                            return float(chosen)
                        else:
                            # ambiguous / implausible -> mark as nan (to be imputed later)
                            return np.nan

                    # Symmetric case: scheduled is time-only but actual has a date
                    if hasattr(s, 'year') and s.year == 1900 and hasattr(a, 'year') and a.year != 1900:
                        base = s.replace(year=a.year, month=a.month, day=a.day)
                        cand_same = base
                        cand_next = base + pd.Timedelta(days=1)
                        delta_same = (a - cand_same).total_seconds() / 60.0
                        delta_next = (a - cand_next).total_seconds() / 60.0
                        candidates = [(abs(delta_same), delta_same), (abs(delta_next), delta_next)]
                        candidates.sort(key=lambda x: x[0])
                        chosen = candidates[0][1]
                        if abs(chosen) <= 720:
                            return float(chosen)
                        else:
                            return np.nan

                    # Default: both have dates or compatible times
                    delta = (a - s).total_seconds() / 60.0
                    return float(delta)
                except Exception:
                    return np.nan

            df['delay_minutes'] = df.apply(_compute_delay, axis=1)
            self.cleaning_steps.append('computed_delay_from_times')

            # flag rows where delay could not be computed (NaN) so we can impute later
            df['delay_computed'] = df['delay_minutes'].notna()

            # After finishing computations, if any delays are extremely large (>|12 hours|) mark them for review
            df['delay_flagged'] = df['delay_minutes'].abs().gt(720).fillna(False)
            # Set flagged extremes to NaN to avoid silently poisoning downstream models
            df.loc[df['delay_flagged'], 'delay_minutes'] = np.nan
            if df['delay_flagged'].any():
                self.cleaning_steps.append('flagged_extreme_delays')

        # Fix negative passenger counts (set to median of non-negative values)
        if 'passenger_count' in df.columns:
            df['passenger_count'] = pd.to_numeric(df['passenger_count'], errors='coerce')
            mask_neg = df['passenger_count'] < 0
            if mask_neg.any():
                median_val = df.loc[~mask_neg, 'passenger_count'].median()
                if pd.isna(median_val):
                    median_val = 0.0
                df.loc[mask_neg, 'passenger_count'] = median_val
                self.cleaning_steps.append('fixed_negative_passenger_count')

        # Clean coordinates: treat sentinel values like 999 or 0.0 as NaN
        for coord in ('latitude', 'longitude'):
            if coord in df.columns:
                df[coord] = pd.to_numeric(df[coord], errors='coerce')
                mask_bad = df[coord].isin([999, 0])
                if mask_bad.any():
                    df.loc[mask_bad, coord] = np.nan
                    self.cleaning_steps.append(f'cleaned_{coord}_sentinel')

        # Ensure delay-related flags exist even if no time columns were present
        if 'delay_minutes' not in df.columns:
            df['delay_minutes'] = np.nan
        if 'delay_flagged' not in df.columns:
            df['delay_flagged'] = False
        if 'delay_computed' not in df.columns:
            df['delay_computed'] = df['delay_minutes'].notna()
        if 'delay_imputed' not in df.columns:
            df['delay_imputed'] = False

        # Fill NaNs for numeric columns with sensible defaults (median)
        # NOTE: exclude 'delay_minutes' from generic fill so we can handle imputation policy explicitly
        num_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c != 'delay_minutes']
        for c in num_cols:
            if df[c].isna().any():
                med = df[c].median()
                if pd.isna(med):
                    med = 0.0
                df[c] = df[c].fillna(med)

        # Handle delay_minutes imputation policy:
        # - Rows where delay_flagged==True should remain NaN for manual review
        # - Other NaN delays will be imputed with the median of non-NaN, non-flagged delays
        if 'delay_minutes' in df.columns:
            # compute median excluding NaNs and flagged rows
            med = df.loc[~df['delay_flagged'], 'delay_minutes'].median()
            if pd.isna(med):
                med = 0.0
            # mark rows that will be imputed
            mask_impute = df['delay_minutes'].isna() & (~df['delay_flagged'])
            df.loc[mask_impute, 'delay_minutes'] = med
            df['delay_imputed'] = mask_impute
            # for flagged rows, ensure delay_imputed is False (they remain NaN)
            df.loc[df['delay_flagged'], 'delay_imputed'] = False
        # Weather normalization and typo fixes
        if 'weather' in df.columns:
            def _norm_weather(x):
                if pd.isna(x):
                    return 'Unknown'
                s = str(x).strip().lower()
                if s in ('nan', '', 'none'):
                    return 'Unknown'
                typos = {
                    'clody': 'cloudy',
                    'suny': 'sunny',
                    'sun': 'sunny',
                    'rain': 'rainy'
                }
                s = typos.get(s, s)
                return s.title()

            df['weather'] = df['weather'].apply(_norm_weather)
            self.cleaning_steps.append('normalized_weather')

        # Consolidate column formats to consistent representations
        #  - scheduled_time/actual_time -> consistent string format
        #  - passenger_count -> integer counts
        #  - latitude/longitude -> floats with fixed precision
        #  - route_id -> normalized 'Route-<n>' or Title-cased string
        def _format_dt_for_output(dt):
            if pd.isna(dt):
                return np.nan
            try:
                # Format as ISO date + 12-hour time with AM/PM (international-friendly)
                if hasattr(dt, 'year') and dt.year != 1900:
                    date_part = f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}"
                    time_part = dt.strftime('%I:%M %p')
                    # remove leading zero from hour for readability e.g. 01:05 -> 1:05
                    if time_part.startswith('0'):
                        time_part = time_part[1:]
                    return f"{date_part} {time_part}"
                time_part = dt.strftime('%I:%M %p')
                if time_part.startswith('0'):
                    time_part = time_part[1:]
                return time_part
            except Exception:
                return np.nan

        if '_scheduled_dt' in df.columns:
            df['scheduled_time'] = df['_scheduled_dt'].apply(_format_dt_for_output)
            self.cleaning_steps.append('standardized_scheduled_time')
        if '_actual_dt' in df.columns:
            df['actual_time'] = df['_actual_dt'].apply(_format_dt_for_output)
            self.cleaning_steps.append('standardized_actual_time')

        # Passenger counts should be integer-like
        if 'passenger_count' in df.columns:
            # Round and convert to int (counts)
            df['passenger_count'] = df['passenger_count'].round().fillna(0).astype(int)
            self.cleaning_steps.append('standardized_passenger_count')

        # Coordinates: ensure floats and consistent precision
        for coord in ('latitude', 'longitude'):
            if coord in df.columns:
                df[coord] = pd.to_numeric(df[coord], errors='coerce')
                # round to 8 decimals for consistency
                df[coord] = df[coord].round(8)
                self.cleaning_steps.append(f'standardized_{coord}')

        # Normalize route ids: R03 or 03 -> Route-3; keep existing Route-4
        if 'route_id' in df.columns:
            def _norm_route(x):
                if pd.isna(x):
                    return 'Unknown'
                s = str(x).strip()
                # match R03, r3, 03 etc
                m = re.match(r'^[rR]?(0*)(\d+)$', s)
                if m:
                    return f'Route-{int(m.group(2))}'
                # if already contains 'route' keep title-style
                if 'route' in s.lower():
                    return s.title()
                return s

            df['route_id'] = df['route_id'].apply(_norm_route)
            self.cleaning_steps.append('normalized_route_id')

        # Fill undefined values from the original raw dataset when possible
        placeholders = set(['nan', 'none', '', 'na', 'n/a'])
        def _is_placeholder(v):
            return pd.isna(v) or str(v).strip().lower() in placeholders

        for c in df.columns:
            for i, val in df[c].items():
                if (pd.isna(val) or (isinstance(val, str) and val.strip().lower() == 'unknown')):
                    # check raw original
                    if c in self.raw_df.columns:
                        raw_val = self.raw_df.at[i, c]
                        if not _is_placeholder(raw_val):
                            # standardize raw_val depending on column
                            if c in ('scheduled_time', 'actual_time'):
                                parsed = _parse_time(raw_val)
                                if not pd.isna(parsed):
                                    df.at[i, c] = _format_dt_for_output(parsed)
                                else:
                                    df.at[i, c] = str(raw_val).strip()
                            elif c in ('latitude', 'longitude'):
                                try:
                                    v = float(raw_val)
                                    df.at[i, c] = round(v, 8)
                                except Exception:
                                    df.at[i, c] = raw_val
                            elif c == 'passenger_count':
                                try:
                                    v = float(raw_val)
                                    df.at[i, c] = int(round(v))
                                except Exception:
                                    df.at[i, c] = raw_val
                            elif c == 'weather':
                                df.at[i, c] = _norm_weather(raw_val)
                            elif c == 'route_id':
                                df.at[i, c] = _norm_route(raw_val) if 'route' in locals() else str(raw_val).strip()
                            else:
                                df.at[i, c] = raw_val
        self.cleaning_steps.append('filled_from_raw_where_possible')

        self.df = df
        return df

    def get_cleaning_summary(self):
        return {
            'cleaning_steps': self.cleaning_steps,
            'n_rows': len(self.df),
            'n_cols': len(self.df.columns)
        }
