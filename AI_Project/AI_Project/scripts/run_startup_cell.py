import sys
from pathlib import Path
# make project root importable when running as a script
sys.path.append(str(Path(__file__).resolve().parents[1] / 'src'))
from transport_analysis.data_cleaner import DataCleaner
import pandas as pd

if __name__ == '__main__':
    data = pd.read_csv('dirty_transport_dataset.csv')
    cleaner = DataCleaner(data)
    cleaned = cleaner.run_full_cleaning_pipeline()
    print('Cleaned data shape:', cleaned.shape)
    print('Cleaning steps:', cleaner.get_cleaning_summary()['cleaning_steps'])
    print('\n--- cleaned head ---')
    print(cleaned.head(10).to_string())
