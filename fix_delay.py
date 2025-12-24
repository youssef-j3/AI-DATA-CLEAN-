import pandas as pd

df = pd.read_csv('results/cleaned_transport_data.csv')

print("Rows with negative delay_minutes:")
print(df[df['delay_minutes'] < 0])

df['delay_minutes'] = df['delay_minutes'].clip(lower=0)

df.to_csv('results/cleaned_transport_data.csv', index=False)
print("\nFixed negative values (set to 0)")
