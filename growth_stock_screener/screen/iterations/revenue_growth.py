import pandas as pd
from typing import Dict
from tqdm import tqdm
from termcolor import cprint, colored
import time
from .utils import *
from ..settings import min_growth_percent, protected_rs

# print header message to terminal
process_name = "Revenue Growth"
process_stage = 4
print_status(process_name, process_stage, True)
print_minimums(
    {
        "quarterly revenue growth": f"{min_growth_percent}%",
    },
    newline=False,
)
print(
    colored("Minimum RS rating to bypass revenue screen:", "dark_grey"),
    colored(protected_rs, "light_grey"),
    "\n",
)

# record start time
start = time.perf_counter()

# Check if we can use cached results
current_settings = get_current_settings()
iteration_name = "revenue_growth"

if should_skip_iteration(iteration_name, current_settings):
    print(colored("Using cached revenue growth data from today...", "light_green"))
    screened_df = open_outfile(iteration_name)

    # Skip to the end
    end = time.perf_counter()
    cprint(f"{len(screened_df)} symbols loaded from cache.", "green")
    print_status(process_name, process_stage, False, end - start)
    print_divider()
else:
    # logging data (printed to console after screen finishes)
    logs = []

    # retreive JSON data from previous screen iteration
    df = open_outfile("trend")

    # populate these lists while iterating through symbols
    successful_symbols = []
    failed_symbols = []

    # fetch revenue data for all symbols
    symbol_list = [] if ("Symbol" not in df) else list(df["Symbol"])
    revenue_data = fetch_all_revenues(symbol_list)


def revenue_growth(timeframe: str, df: pd.DataFrame) -> Dict[str, float]:
    """Calculate the revenue growth for the given timeframe compared to the same timeframe one year earlier."""
    if timeframe is None:
        return None

    # fetch revenues for the inputted timeframe and the same timeframe 1 year ago
    prev_timeframe = previous_timeframe(timeframe)
    revenue = extract_revenue(timeframe, df)
    prev_revenue = extract_revenue(prev_timeframe, df)

    # handle cases where data is unavailable or growth is incalculable
    if (revenue is None) or (prev_revenue is None) or (prev_revenue <= 0):
        return None

    # return a dictionary containing revenue growth data
    growth = percent_change(prev_revenue, revenue)

    return {"Current": revenue, "Previous": prev_revenue, "Growth": growth}


def extract_comparison_revenues(symbol: str) -> Dict[str, Dict[str, float]]:
    """Extract revenue from the two most recent financial quarters and their corresponding quarters one year ago."""
    revenue_df = revenue_data[symbol]

    if revenue_df is None:
        return None

    if "Foreign Stock" in revenue_df:
        return {"Foreign Stock": {}}

    # extract the two lowest rows of the revenues DataFrame
    q1_row = revenue_df.iloc[-2] if (len(revenue_df) >= 2) else None
    q2_row = revenue_df.iloc[-1] if (len(revenue_df) >= 1) else None

    # determine the timeframe of each row's revenue report
    q1_timeframe = q1_row["frame"] if (q1_row is not None) else None
    q2_timeframe = q2_row["frame"] if (q2_row is not None) else None

    # calculate the revenue growth for each timeframe compared to the same timeframe 1 year ago
    q1_growth = revenue_growth(q1_timeframe, revenue_df)
    q2_growth = revenue_growth(q2_timeframe, revenue_df)

    # return revenue details as a dictionary
    if q2_growth is None:
        return None

    if q1_growth is None:
        return {"Q2": q2_growth}

    return {
        "Q1": q1_growth,
        "Q2": q2_growth,
    }


def screen_revenue_growth(df_index: int) -> None:
    """Populate stock data lists based on whether the given dataframe row has strong revenue growth."""
    row = df.iloc[df_index]

    symbol = row["Symbol"]
    rs = row["RS"]
    revenues = extract_comparison_revenues(symbol)

    # handle null values from missing data
    if revenues is None:
        logs.append(skip_message(symbol, "insufficient data"))
        failed_symbols.append(symbol)
        return

    if "Foreign Stock" in revenues:
        logs.append(skip_message(symbol, "foreign stock"))
        return

    # print revenue growth data to console
    if "Q1" in revenues:
        logs.append(
            f"""\n{symbol} | Q1 revenue growth: {revenues["Q1"]["Growth"]:.0f}%, Q2 revenue growth: {revenues["Q2"]["Growth"]:.0f}%, RS: {rs}
            Q1 : current revenue: ${revenues["Q1"]["Current"]:,.0f}, previous revenue: ${revenues["Q1"]["Previous"]:,.0f}
            Q2 : current revenue: ${revenues["Q2"]["Current"]:,.0f}, previous revenue: ${revenues["Q2"]["Previous"]:,.0f}\n"""
        )
    else:
        logs.append(
            f"""\n{symbol} | Q2 revenue growth: {revenues["Q2"]["Growth"]:.0f}%, RS: {rs}
            Q2 : current revenue: ${revenues["Q2"]["Current"]:,.0f}, previous revenue: ${revenues["Q2"]["Previous"]:,.0f}\n"""
        )

    # filter out stocks with low quarterly revenue growth
    if (revenues["Q2"]["Growth"] < min_growth_percent) and (rs < protected_rs):
        logs.append(filter_message(symbol))
        return

    if (
        ("Q1" in revenues)
        and (revenues["Q1"]["Growth"] < min_growth_percent)
        and (rs < protected_rs)
    ):
        logs.append(filter_message(symbol))
        return

    successful_symbols.append(
        {
            "Symbol": symbol,
            "Company Name": row["Company Name"],
            "Industry": row["Industry"],
            "RS": rs,
            "Price": row["Price"],
            "Market Cap": row["Market Cap"],
            "Revenue Growth % (most recent Q)": revenues["Q2"]["Growth"],
            "Revenue Growth % (previous Q)": "N/A"
            if ("Q1" not in revenues)
            else revenues["Q1"]["Growth"],
            "50-day Average Volume": row["50-day Average Volume"],
            "% Below 52-week High": row["% Below 52-week High"],
        }
    )


if not should_skip_iteration(iteration_name, current_settings):
    # screen each stock present in the DataFrame
    print("\nScreening stocks . . .\n")
    for i in tqdm(range(0, len(df))):
        screen_revenue_growth(i)

    # create a new dataframe with symbols which satisfied revenue_growth criteria
    screened_df = pd.DataFrame(successful_symbols)

    # serialize data in JSON format and save on machine
    create_outfile(screened_df, "revenue_growth")

    # Mark this iteration as complete in the cache
    mark_iteration_complete(iteration_name)

    # print log
    print("".join(logs))

    # record end time
    end = time.perf_counter()

    # print footer message to terminal
    cprint(
        f"{len(failed_symbols)} symbols failed (insufficient revenue reports).", "dark_grey"
    )
    cprint(
        f"{len(df) - len(screened_df) - len(failed_symbols)} symbols filtered (revenue growth too low or foreign stock).",
        "dark_grey",
    )
    cprint(f"{len(screened_df)} symbols passed.", "green")
    print_status(process_name, process_stage, False, end - start)
    print_divider()
