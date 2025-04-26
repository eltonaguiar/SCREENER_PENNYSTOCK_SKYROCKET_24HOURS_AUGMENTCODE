from screen.iterations.utils import *
import os
import time
from datetime import datetime
from termcolor import colored

print("\n\nStarting simplified stock screener...\n")

# Initialize cache with current settings
current_settings = get_current_settings()
save_cache_settings(current_settings)
print(colored("Cache initialized with current settings.", "light_grey"))

# Run each stage manually
try:
    # Stage 0: NASDAQ Listings
    print("\nRunning Stage 0: NASDAQ Listings...")
    import screen.iterations.nasdaq_listings
    
    # Stage 1: Relative Strength
    print("\nRunning Stage 1: Relative Strength...")
    import screen.iterations.relative_strength
    
    # Stage 2: Liquidity
    print("\nRunning Stage 2: Liquidity...")
    import screen.iterations.liquidity
    
    # Stage 3: Trend
    print("\nRunning Stage 3: Trend...")
    import screen.iterations.trend
    
    # Stage 4: Revenue Growth
    print("\nRunning Stage 4: Revenue Growth...")
    import screen.iterations.revenue_growth
    
    # Stage 5: Institutional Accumulation
    print("\nRunning Stage 5: Institutional Accumulation...")
    import screen.iterations.institutional_accumulation
    
    # Open final results
    final_iteration = "institutional_accumulation"
    df = open_outfile(final_iteration)
    
    # Create output files
    time_string = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    outfile_name = f"screen_results {time_string}.csv"
    df.to_csv(outfile_name)
    
    # Create summary Excel file
    print("\nCreating summary Excel file...")
    summary_file = create_summary_file()
    print(f"Summary file created: {summary_file}")
    
    # Create detailed analysis
    print("\nCreating detailed symbols analysis...")
    analysis_file = analyze_symbols()
    if analysis_file:
        print(f"Symbols analysis created: {analysis_file}")
        # Open the analysis file in the default browser
        import webbrowser
        webbrowser.open(f"file://{os.path.abspath(analysis_file)}")
    
    print("\nScreening completed successfully!")
    print(f"Found {len(df)} stocks under $4 with high growth potential.")
    print(f"Results saved to: {outfile_name}")
    
except Exception as e:
    print(f"\nError during screening: {e}")
    import traceback
    traceback.print_exc()
