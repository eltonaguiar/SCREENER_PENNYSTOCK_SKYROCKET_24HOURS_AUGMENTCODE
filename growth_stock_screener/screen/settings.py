import multiprocessing

# ITERATIONS (modify these values as desired)

# Iteration 1: Relative Strength
min_rs: int = 80  # minimum RS rating to pass (integer from 0-100) - lowered to include more candidates

# Iteration 2: Liquidity
min_market_cap: float = 10000000   # minimum market cap (USD) - lowered to $10M to include more micro-cap companies
min_price: float = 0.20            # minimum price (USD) - lowered to $0.20 to include more penny stocks
max_price: float = 4.00            # maximum price (USD) - kept at $4
min_volume: int = 10000            # minimum 50-day average volume - lowered to include more thinly traded stocks

# Iteration 3: Trend
trend_settings = {
    "Price >= 50-day SMA": False,              # set values to 'True' or 'False' - relaxed to include stocks in pullbacks
    "Price >= 200-day SMA": False,             # ^ - relaxed to allow for newer breakouts
    "10-day SMA >= 20-day SMA": False,         # ^ - relaxed to include stocks in consolidation
    "20-day SMA >= 50-day SMA": False,         # ^ - relaxed to include stocks in consolidation
    "Price within 50% of 52-week High": True,  # ^ - kept to ensure stocks aren't too far from highs
}

# Iteration 4: Revenue Growth
min_growth_percent: float = 20  # minimum revenue growth for a quarter compared to the same quarter 1 year ago (percentage) - lowered to include more candidates
protected_rs: int = 90          # minimum RS rating to bypass revenue screen iteration (see README) - lowered to include more candidates

# Iteration 5: Institutional Accumulation
# (no parameters to modify)

# THREADS (manually set the following value if the screener reports errors during the "Trend" or "Institutional Accumulation" iterations)
# Recommended values are 1-10. Currently set to 3/4 the number of CPU cores on the system (with a max of 10)

# Thread Pool Size
threads: int = min(int(multiprocessing.cpu_count() * 0.75), 10)  # number of concurrent browser instances to fetch dynamic data (positive integer)
