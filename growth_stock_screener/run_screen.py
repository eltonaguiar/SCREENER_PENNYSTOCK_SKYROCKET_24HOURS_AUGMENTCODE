from screen.iterations.utils import *
from datetime import datetime
import time
import os
from termcolor import cprint, colored

# constants
current_time = datetime.now()

# print banner and heading
print_banner()
print_settings(current_time)

# check Python version
min_python_version = "3.11"
assert_python_updated(min_python_version)

# Initialize cache with current settings
current_settings = get_current_settings()
save_cache_settings(current_settings)
print(colored("\nCache initialized with current settings.", "light_grey"))
print(colored("Results from previous runs with the same settings today will be reused.", "light_grey"))

# Skip waiting for user input in automated mode
print("\nStarting screen automatically...")

# track start time
start = time.perf_counter()

# run screen iterations
import screen.iterations.nasdaq_listings
import screen.iterations.relative_strength
import screen.iterations.liquidity
import screen.iterations.trend
import screen.iterations.revenue_growth
import screen.iterations.institutional_accumulation

# open screen results as a DataFrame
final_iteration = "institutional_accumulation"
df = open_outfile(final_iteration)

# create a .csv outfile
time_string = current_time.strftime("%Y-%m-%d %H-%M-%S")
outfile_name = f"screen_results {time_string}.csv"
df.to_csv(outfile_name)

# create a summary Excel file with tabs for each stage
print("\nCreating summary Excel file...")
summary_file = create_summary_file()
print(f"Summary file created: {summary_file}")

# create a detailed analysis of the symbols
print("\nCreating detailed symbols analysis...")
analysis_file = analyze_symbols()
if analysis_file:
    print(f"Symbols analysis created: {analysis_file}")
    # Open the analysis file in the default browser
    import webbrowser
    webbrowser.open(f"file://{os.path.abspath(analysis_file)}")

# track end time
end = time.perf_counter()

# notify user when finished
print_done_message(end - start, outfile_name)
