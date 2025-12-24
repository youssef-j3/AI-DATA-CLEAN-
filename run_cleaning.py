import pandas as pd
from src.transport_analysis.data_loader import DataLoader
from src.transport_analysis.data_cleaner import DataCleaner
from src.transport_analysis.feature_engineer import FeatureEngineer

# Load dirty data
loader = DataLoader('dirty_transport_dataset.csv')
df = loader.load_data()

# Clean data
cleaner = DataCleaner(df)
cleaned_df = cleaner.run_full_cleaning_pipeline()

# Save cleaned data
cleaned_df.to_csv('results/cleaned_transport_data.csv', index=False)

# Feature engineering
engineer = FeatureEngineer(cleaned_df)
engineered_df = engineer.run_full_feature_engineering()

# Save engineered data
engineered_df.to_csv('results/engineered_transport_data.csv', index=False)

print("Data cleaning and feature engineering completed!")
print(f"Cleaned data shape: {cleaned_df.shape}")
print(f"Engineered data shape: {engineered_df.shape}")
