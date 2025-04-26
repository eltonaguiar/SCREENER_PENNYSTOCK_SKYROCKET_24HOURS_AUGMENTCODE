from screen.iterations.utils import *
import pandas as pd
import os
import time
from termcolor import colored

print("Testing institutional accumulation stage...")

# Create a sample DataFrame for testing
data = {
    'Symbol': ['AAPL', 'MSFT', 'GOOGL'],
    'Company Name': ['Apple Inc.', 'Microsoft Corporation', 'Alphabet Inc.'],
    'Industry': ['Consumer Electronics', 'Software', 'Internet Content & Information'],
    'RS': [95, 92, 88],
    'Price': [3.50, 2.75, 3.25],
    'Market Cap': [2500000000, 1800000000, 2200000000],
    '50-day Average Volume': [15000000, 12000000, 8000000],
    '% Below 52-week High': [-15, -12, -18],
    'Revenue Growth % (most recent Q)': [15, 12, 18],
    'Revenue Growth % (previous Q)': [10, 8, 14]
}

df = pd.DataFrame(data)

# Create the json directory if it doesn't exist
json_dir = os.path.join(os.getcwd(), "json")
if not os.path.exists(json_dir):
    os.makedirs(json_dir)

# Save the DataFrame as a JSON file
create_outfile(df, "revenue_growth")

# Import the institutional_accumulation module
print("Importing institutional_accumulation module...")
import screen.iterations.institutional_accumulation as inst_acc

# Check if the module was imported successfully
print("Module imported successfully!")
print(f"Number of symbols to process: {len(df)}")

# Check the results
print("\nChecking results...")
try:
    result_df = open_outfile("institutional_accumulation")
    print(f"Number of symbols in result: {len(result_df)}")
    print("Symbols in result:")
    for i, row in result_df.iterrows():
        print(f"  {row['Symbol']}: {row['Company Name']}")
except Exception as e:
    print(f"Error opening result file: {e}")

print("\nTest completed!")
