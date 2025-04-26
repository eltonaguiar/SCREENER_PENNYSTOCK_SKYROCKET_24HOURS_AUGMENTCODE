from screen.iterations.utils import *
import os
from datetime import datetime

print("Starting analysis...")

try:
    # Create a sample DataFrame for testing
    data = {
        'Symbol': ['AAPL', 'MSFT', 'GOOGL'],
        'Company Name': ['Apple Inc.', 'Microsoft Corporation', 'Alphabet Inc.'],
        'Industry': ['Consumer Electronics', 'Software', 'Internet Content & Information'],
        'RS': [95, 92, 88],
        'Price': [3.50, 2.75, 3.25],
        'Market Cap': [2500000000, 1800000000, 2200000000],
        '50-day Average Volume': [15000000, 12000000, 8000000],
        '% Below 52-week High': [-15, -12, -18]
    }
    
    df = pd.DataFrame(data)
    
    # Create the json directory if it doesn't exist
    json_dir = os.path.join(os.getcwd(), "json")
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)
    
    # Save the DataFrame as a JSON file
    create_outfile(df, "institutional_accumulation")
    
    # Create a summary Excel file
    print("\nCreating summary Excel file...")
    summary_file = create_summary_file()
    print(f"Summary file created: {summary_file}")
    
    # Create a detailed analysis of the symbols
    print("\nCreating detailed symbols analysis...")
    analysis_file = analyze_symbols()
    if analysis_file:
        print(f"Symbols analysis created: {analysis_file}")
        # Open the analysis file in the default browser
        import webbrowser
        webbrowser.open(f"file://{os.path.abspath(analysis_file)}")
    
    print("Analysis completed successfully!")
    
except Exception as e:
    print(f"Error during analysis: {e}")
    import traceback
    traceback.print_exc()
