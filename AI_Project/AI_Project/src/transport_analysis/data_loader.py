import pandas as pd


class DataLoader:
    def __init__(self, path):
        self.path = path

    def load_data(self):
        """Load CSV data path and return a DataFrame."""
        return pd.read_csv(self.path)
