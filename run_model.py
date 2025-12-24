import pandas as pd
from src.transport_analysis.model_builder import ModelBuilder

df = pd.read_csv('results/engineered_transport_data.csv')
mb = ModelBuilder(df)
results = mb.run_all_models()
print(results)
