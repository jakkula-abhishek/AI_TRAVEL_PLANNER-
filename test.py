import pandas as pd

# Load JSON dataset
tourism = pd.read_json("data/india_tourism_dataset.json")

print("Tourism Columns:")
print(tourism.columns.tolist())

print("\nFirst 5 rows:")
print(tourism.head())