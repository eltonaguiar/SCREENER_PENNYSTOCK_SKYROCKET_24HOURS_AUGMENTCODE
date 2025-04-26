# IDEAS.MD - Growth Stock Screener Enhancement Proposals

## Current Project Analysis

The Growth Stock Screener currently focuses on finding promising growth stocks with specific characteristics:
- Price range limited to $0.50-$4.00 (lowered from the original higher limits)
- Minimum market cap of $50 million (lowered from $1 billion)
- Minimum volume requirement reduced to 50,000 shares
- Strong relative strength (RS) ratings
- Technical trend criteria
- Revenue growth metrics
- Institutional accumulation signals

This configuration suggests the screener is being used to find lower-priced growth stocks with potential for significant upward movement, possibly targeting penny stocks or small caps with growth characteristics.

## Enhancement Ideas

### 1. Advanced Price Range Flexibility

#### Implementation:
```python
# Price Range Presets
price_range_presets = {
    "penny_stocks": {"min": 0.10, "max": 5.00},
    "small_cap_value": {"min": 5.00, "max": 20.00},
    "mid_cap_growth": {"min": 20.00, "max": 100.00},
    "blue_chip": {"min": 100.00, "max": 10000.00},
    "custom": {"min": min_price, "max": max_price}  # User's custom range
}

# Active preset (can be changed via command line argument)
active_price_preset = "penny_stocks"  # Default
```

Add a command-line interface to select price ranges:

```python
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description='Run Growth Stock Screener with specific settings')
    parser.add_argument('--price-preset', type=str, choices=list(price_range_presets.keys()),
                        help='Select a price range preset')
    parser.add_argument('--min-price', type=float, help='Set custom minimum price')
    parser.add_argument('--max-price', type=float, help='Set custom maximum price')
    
    return parser.parse_args()

args = parse_arguments()
if args.price_preset:
    from screen.settings import price_range_presets
    active_price_preset = args.price_preset
    # Update the current min and max price settings
    if args.price_preset != "custom":
        min_price = price_range_presets[active_price_preset]["min"]
        max_price = price_range_presets[active_price_preset]["max"]
    elif args.min_price is not None and args.max_price is not None:
        min_price = args.min_price
        max_price = args.max_price
```

### 2. Strategy Picker with Pre-defined Investment Styles

Add different screening strategies that users can select:

```python
# Strategy Presets
strategy_presets = {
    "momentum": {
        "min_rs": 95,
        "trend_settings": {
            "Price >= 50-day SMA": True,
            "Price >= 200-day SMA": True,
            "10-day SMA >= 20-day SMA": True,
            "20-day SMA >= 50-day SMA": True,
            "Price within 50% of 52-week High": True
        },
        "min_growth_percent": 25,
        "protected_rs": 98
    },
    "value_growth": {
        "min_rs": 80,
        "trend_settings": {
            "Price >= 50-day SMA": True,
            "Price >= 200-day SMA": False,
            "10-day SMA >= 20-day SMA": True,
            "20-day SMA >= 50-day SMA": False,
            "Price within 50% of 52-week High": True
        },
        "min_growth_percent": 15,
        "protected_rs": 90
    },
    "breakout": {
        "min_rs": 90,
        "trend_settings": {
            "Price >= 50-day SMA": True,
            "Price >= 200-day SMA": False,
            "10-day SMA >= 20-day SMA": True,
            "20-day SMA >= 50-day SMA": True,
            "Price within 50% of 52-week High": True
        },
        "min_growth_percent": 30,
        "protected_rs": 95
    },
    "custom": {
        # Current user settings as default
        "min_rs": min_rs,
        "trend_settings": trend_settings,
        "min_growth_percent": min_growth_percent,
        "protected_rs": protected_rs
    }
}

active_strategy = "custom"  # Default to custom (current settings)
```

### 3. Performance Backtesting Module

Create a new module to backtest the performance of screened stocks:

```python
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
from termcolor import colored, cprint

def backtest_portfolio(symbols, investment_per_stock=100, start_date=None, end_date=None, benchmark="SPY"):
    """
    Backtest a portfolio of stocks with equal investment in each.
    
    Parameters:
    -----------
    symbols : list
        List of stock symbols to backtest
    investment_per_stock : float
        Amount to invest in each stock
    start_date : datetime
        Start date for backtesting (defaults to 30 days ago)
    end_date : datetime
        End date for backtesting (defaults to today)
    benchmark : str
        Symbol for benchmark comparison (default: SPY)
    """
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
        
    print(f"Backtesting portfolio of {len(symbols)} stocks from {start_date} to {end_date}...")
    
    # Add benchmark to symbols
    all_symbols = symbols + [benchmark]
    
    # Download price data
    prices = yf.download(all_symbols, start=start_date, end=end_date)['Adj Close']
    
    # Calculate returns
    returns = prices.pct_change().dropna()
    
    # Calculate portfolio performance
    portfolio_values = pd.DataFrame(index=returns.index)
    
    # Calculate shares purchased for each stock
    shares = {}
    for symbol in symbols:
        if symbol in prices.columns and not pd.isna(prices[symbol].iloc[0]):
            shares[symbol] = investment_per_stock / prices[symbol].iloc[0]
        else:
            shares[symbol] = 0
    
    # Calculate daily portfolio value
    portfolio_values['Portfolio'] = 0
    for symbol in symbols:
        if symbol in prices.columns and shares[symbol] > 0:
            portfolio_values['Portfolio'] += prices[symbol] * shares[symbol]
    
    # Calculate benchmark performance (normalized to same starting investment)
    total_investment = investment_per_stock * len(symbols)
    benchmark_shares = total_investment / prices[benchmark].iloc[0]
    portfolio_values['Benchmark'] = prices[benchmark] * benchmark_shares
    
    # Calculate portfolio metrics
    portfolio_returns = portfolio_values.pct_change().dropna()
    
    # Calculate Sharpe ratio (assuming risk-free rate of 0% for simplicity)
    sharpe_ratio = np.sqrt(252) * portfolio_returns['Portfolio'].mean() / portfolio_returns['Portfolio'].std()
    
    # Calculate max drawdown
    portfolio_cumulative = (1 + portfolio_returns['Portfolio']).cumprod()
    running_max = portfolio_cumulative.cummax()
    drawdown = (portfolio_cumulative / running_max) - 1
    max_drawdown = drawdown.min()
    
    # Calculate total return
    total_return = (portfolio_values['Portfolio'].iloc[-1] / portfolio_values['Portfolio'].iloc[0]) - 1
    benchmark_return = (portfolio_values['Benchmark'].iloc[-1] / portfolio_values['Benchmark'].iloc[0]) - 1
    
    # Plot results
    plt.figure(figsize=(10, 6))
    plt.plot(portfolio_values.index, portfolio_values['Portfolio'], label=f'Screened Portfolio ({total_return:.2%})')
    plt.plot(portfolio_values.index, portfolio_values['Benchmark'], label=f'{benchmark} ({benchmark_return:.2%})')
    plt.title(f'Portfolio Performance vs {benchmark} ({start_date} to {end_date})')
    plt.ylabel('Portfolio Value ($)')
    plt.xlabel('Date')
    plt.legend()
    plt.grid(True)
    plt.savefig(f'backtest_results_{datetime.now().strftime("%Y-%m-%d")}.png')
    
    # Print results
    print("\n" + "="*50)
    print(colored("BACKTEST RESULTS", "light_green", attrs=["bold"]))
    print("="*50)
    print(f"Time Period: {start_date} to {end_date}")
    print(f"Number of Stocks: {len(symbols)}")
    print(f"Investment per Stock: ${investment_per_stock:.2f}")
    print(f"Total Investment: ${total_investment:.2f}")
    
    print("\nPERFORMANCE METRICS:")
    print(f"Total Return: {total_return:.2%}" + 
          colored(f" (vs {benchmark}: {benchmark_return:.2%})", 
                 "green" if total_return > benchmark_return else "red"))
    print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
    print(f"Maximum Drawdown: {max_drawdown:.2%}")
    
    # Return the results
    return {
        "total_return": total_return,
        "benchmark_return": benchmark_return,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown": max_drawdown,
        "portfolio_values": portfolio_values
    }

def run_backtest():
    # Load the most recent screen results
    import os
    import glob
    
    # Find most recent CSV file in root directory
    csv_files = glob.glob("screen_results*.csv")
    most_recent_csv = max(csv_files, key=os.path.getctime) if csv_files else None
    
    if most_recent_csv:
        results = pd.read_csv(most_recent_csv)
        symbols = results['Symbol'].tolist()
        
        # Ask for backtest parameters
        print(colored(f"\nFound {len(symbols)} stocks in {most_recent_csv}", "light_green"))
        investment = float(input("Investment per stock ($): ") or "100")
        days = int(input("Number of days to backtest: ") or "30")
        benchmark = input("Benchmark symbol (default: SPY): ") or "SPY"
        
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Run backtest
        backtest_portfolio(symbols, investment, start_date, end_date, benchmark)
    else:
        print(colored("No screen results found. Run the screener first.", "red"))

if __name__ == "__main__":
    run_backtest()
```

Add an entry point in the main file:

```python
# Add to imports
import argparse

# Add this function
def parse_arguments():
    parser = argparse.ArgumentParser(description='Growth Stock Screener')
    parser.add_argument('--backtest', action='store_true', help='Run backtest on most recent results')
    # Add other arguments
    return parser.parse_args()

# Add near the top
args = parse_arguments()
if args.backtest:
    from growth_stock_screener.backtest.backtest_results import run_backtest
    run_backtest()
    sys.exit(0)
```

### 4. Momentum and Technical Indicators Module

Add advanced technical indicators for better stock selection:

```python
import pandas as pd
import numpy as np
import talib  # Technical Analysis Library
from datetime import datetime
import time
from termcolor import cprint, colored
from .utils import *
from ..settings import *

# Initialize new settings
# Settings for momentum indicators
momentum_settings = {
    "min_rsi": 50,  # Minimum RSI value (0-100)
    "max_rsi": 80,  # Maximum RSI value (0-100)
    "rsi_period": 14,  # Period for RSI calculation
    "macd_fast": 12,  # Fast period for MACD
    "macd_slow": 26,  # Slow period for MACD
    "macd_signal": 9,  # Signal period for MACD
    "min_adx": 25,  # Minimum ADX value to indicate strong trend
    "adx_period": 14,  # Period for ADX calculation
    "required_indicators": {  # Which indicators must be positive
        "rsi": True,  # RSI within range
        "macd": True,  # MACD positive/signal cross
        "adx": True,  # ADX above threshold
        "volatility": False  # Check if volatility is acceptable
    }
}

# print header message to terminal
process_name = "Momentum Indicators"
process_stage = 6  # Make this the last step
print_status(process_name, process_stage, True)

# Record start time
start = time.perf_counter()

# Check if we can use cached results
current_settings = get_current_settings()
iteration_name = "momentum_indicators"

if should_skip_iteration(iteration_name, current_settings):
    print(colored("Using cached momentum indicator data from today...", "light_green"))
    screened_df = open_outfile(iteration_name)
    
    # Skip to the end
    end = time.perf_counter()
    cprint(f"{len(screened_df)} symbols loaded from cache.", "green")
    print_status(process_name, process_stage, False, end - start)
    print_divider()
else:
    # logging data
    logs = []
    
    # retrieve JSON data from previous screen iteration
    df = open_outfile("institutional_accumulation")
    
    # populate lists while iterating through symbols
    successful_symbols = []
    failed_symbols = []
    
    # Download historical price data for all symbols
    symbol_list = list(df["Symbol"])
    print("\nFetching historical price data for momentum indicators...\n")
    
    import yfinance as yf
    
    # Download data in one batch
    stock_data = yf.download(symbol_list, period="60d", interval="1d")
    
    def calculate_indicators(symbol):
        """Calculate technical indicators for a given symbol"""
        try:
            # Extract price data for this symbol
            close_prices = stock_data['Close'][symbol].values
            high_prices = stock_data['High'][symbol].values
            low_prices = stock_data['Low'][symbol].values
            volume = stock_data['Volume'][symbol].values
            
            # Calculate RSI
            rsi = talib.RSI(close_prices, timeperiod=momentum_settings["rsi_period"])
            current_rsi = rsi[-1]
            
            # Calculate MACD
            macd, macd_signal, macd_hist = talib.MACD(
                close_prices,
                fastperiod=momentum_settings["macd_fast"],
                slowperiod=momentum_settings["macd_slow"],
                signalperiod=momentum_settings["macd_signal"]
            )
            current_macd = macd[-1]
            current_signal = macd_signal[-1]
            current_hist = macd_hist[-1]
            
            # Calculate ADX (Average Directional Index)
            adx = talib.ADX(high_prices, low_prices, close_prices, timeperiod=momentum_settings["adx_period"])
            current_adx = adx[-1]
            
            # Calculate Bollinger Bands
            upper, middle, lower = talib.BBANDS(close_prices, timeperiod=20)
            current_upper = upper[-1]
            current_middle = middle[-1]
            current_lower = lower[-1]
            
            # Calculate volatility (standard deviation of returns)
            returns = np.diff(close_prices) / close_prices[:-1]
            volatility = np.std(returns) * np.sqrt(252)  # Annualized
            
            # Check momentum conditions
            momentum_conditions = {
                "rsi": momentum_settings["min_rsi"] <= current_rsi <= momentum_settings["max_rsi"],
                "macd": current_hist > 0 and current_macd > current_signal,
                "adx": current_adx > momentum_settings["min_adx"],
                "volatility": volatility < 0.8  # This threshold might need adjustment
            }
            
            # Determine if stock passes based on required indicators
            passes = True
            for indicator, required in momentum_settings["required_indicators"].items():
                if required and not momentum_conditions[indicator]:
                    passes = False
                    break
            
            return {
                "symbol": symbol,
                "rsi": current_rsi,
                "macd": current_hist,
                "adx": current_adx,
                "volatility": volatility,
                "passes": passes,
                "momentum_conditions": momentum_conditions
            }
            
        except Exception as e:
            logs.append(skip_message(symbol, str(e)))
            return {
                "symbol": symbol,
                "passes": False,
                "error": str(e)
            }
    
    print("Calculating momentum indicators...\n")
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from tqdm import tqdm
    
    # Process all symbols with progress bar
    results = []
    with ThreadPoolExecutor(max_workers=threads) as executor:
        future_to_symbol = {executor.submit(calculate_indicators, symbol): symbol for symbol in symbol_list}
        for future in tqdm(as_completed(future_to_symbol), total=len(symbol_list)):
            result = future.result()
            results.append(result)
    
    # Process results
    for result in results:
        symbol = result["symbol"]
        if not result.get("passes", False):
            if "error" in result:
                failed_symbols.append(symbol)
            else:
                logs.append(filter_message(symbol))
            continue
        
        # Get original row data
        row = df[df["Symbol"] == symbol].iloc[0]
        
        # Add momentum indicators to successful symbols
        successful_symbols.append({
            "Symbol": symbol,
            "Company Name": row["Company Name"],
            "Industry": row["Industry"],
            "RS": row["RS"],
            "Price": row["Price"],
            "Market Cap": row["Market Cap"],
            "50-day Average Volume": row["50-day Average Volume"],
            "Revenue Growth % (most recent Q)": row["Revenue Growth % (most recent Q)"],
            "Revenue Growth % (previous Q)": row["Revenue Growth % (previous Q)"],
            "% Below 52-week High": row["% Below 52-week High"],
            "Net Institutional Inflows": row["Net Institutional Inflows"],
            "RSI": result["rsi"],
            "MACD": result["macd"],
            "ADX": result["adx"],
            "Volatility": result["volatility"]
        })
        
        # Add to logs
        logs.append(
            f"""\n{symbol} | RSI: {result["rsi"]:.1f}, MACD: {result["macd"]:.2f}, ADX: {result["adx"]:.1f}, Volatility: {result["volatility"]:.2f}
            RSI in range: {result["momentum_conditions"]["rsi"]}, MACD positive: {result["momentum_conditions"]["macd"]}, Strong trend: {result["momentum_conditions"]["adx"]}\n"""
        )
    
    # Create dataframe with successful symbols
    screened_df = pd.DataFrame(successful_symbols)
    
    # Serialize data and save
    create_outfile(screened_df, "momentum_indicators")
    
    # Mark iteration as complete in cache
    mark_iteration_complete(iteration_name)
    
    # Print log
    print("".join(logs))
    
    # Record end time
    end = time.perf_counter()
    
    # Print footer message
    cprint(f"{len(failed_symbols)} symbols failed (insufficient data).", "dark_grey")
    cprint(
        f"{len(df) - len(screened_df) - len(failed_symbols)} symbols filtered (poor momentum indicators).",
        "dark_grey",
    )
    cprint(f"{len(screened_df)} symbols passed.", "green")
    print_status(process_name, process_stage, False, end - start)
    print_divider()

# Update the run_screen.py to include this new iteration
# filepath: c:\Users\zerou\Documents\growth-stock-screener\growth_stock_screener\run_screen.py
# Add after institutional_accumulation:
# import screen.iterations.momentum_indicators

# And update the final_iteration variable:
# final_iteration = "momentum_indicators"
```

### 5. Sharpe Ratio Calculation and Stock Ranking

Implement a module to calculate risk-adjusted returns:

```python
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import time
from termcolor import cprint, colored
from tqdm import tqdm
from .utils import *

# print header message to terminal
process_name = "Risk-Adjusted Returns"
process_stage = 7  # Make this the final step
print_status(process_name, process_stage, True)

# record start time
start = time.perf_counter()

# Check if we can use cached results
current_settings = get_current_settings()
iteration_name = "risk_adjusted_returns"

if should_skip_iteration(iteration_name, current_settings):
    print(colored("Using cached risk-adjusted returns data from today...", "light_green"))
    screened_df = open_outfile(iteration_name)
    
    # Skip to the end
    end = time.perf_counter()
    cprint(f"{len(screened_df)} symbols loaded from cache.", "green")
    print_status(process_name, process_stage, False, end - start)
    print_divider()
else:
    # logging data
    logs = []
    
    # Get the previous iteration's dataframe
    # Assumes momentum_indicators is the previous step
    previous_iteration = "institutional_accumulation"  # Or "momentum_indicators" if added
    df = open_outfile(previous_iteration)
    
    # symbols to process
    symbol_list = list(df["Symbol"])
    
    # Get historical data for the past 3 months
    print("Calculating risk-adjusted returns...\n")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)  # 3 months of data
    
    # Download price data for all symbols and SPY (as benchmark)
    symbols_with_spy = symbol_list + ["SPY"]
    historical_data = yf.download(
        symbols_with_spy,
        start=start_date.strftime('%Y-%m-%d'),
        end=end_date.strftime('%Y-%m-%d'),
        progress=False
    )
    
    # Calculate daily returns
    returns = historical_data["Adj Close"].pct_change().dropna()
    
    # Risk-free rate (using 3-month Treasury bill rate, simplified)
    risk_free_rate = 0.05 / 252  # Assuming ~5% annual rate, converted to daily
    
    # Function to calculate Sharpe ratio for a stock
    def calculate_sharpe(symbol):
        try:
            # Get returns for this symbol
            stock_returns = returns[symbol].dropna()
            
            # Need at least 20 days of returns
            if len(stock_returns) < 20:
                return None
            
            # Calculate excess returns
            excess_returns = stock_returns - risk_free_rate
            
            # Calculate Sharpe ratio (annualized)
            sharpe_ratio = np.sqrt(252) * excess_returns.mean() / stock_returns.std()
            
            # Calculate Sortino ratio (downside risk only)
            downside_returns = stock_returns[stock_returns < 0]
            sortino_ratio = np.sqrt(252) * excess_returns.mean() / downside_returns.std() if len(downside_returns) > 0 else np.nan
            
            # Alpha calculation (using SPY as market proxy)
            market_returns = returns["SPY"].dropna()
            
            # Make sure we have matching dates
            aligned_returns = pd.DataFrame({
                'stock': stock_returns,
                'market': market_returns
            }).dropna()
            
            if len(aligned_returns) < 20:
                alpha = np.nan
                beta = np.nan
            else:
                # Calculate beta
                covariance = np.cov(aligned_returns['stock'], aligned_returns['market'])[0, 1]
                market_variance = np.var(aligned_returns['market'])
                beta = covariance / market_variance if market_variance > 0 else np.nan
                
                # Calculate alpha (annualized)
                alpha = (np.mean(aligned_returns['stock']) - risk_free_rate - 
                        beta * (np.mean(aligned_returns['market']) - risk_free_rate)) * 252
            
            return {
                'sharpe_ratio': sharpe_ratio,
                'sortino_ratio': sortino_ratio,
                'alpha': alpha,
                'beta': beta
            }
        except Exception as e:
            logs.append(skip_message(symbol, str(e)))
            return None
    
    # Process each symbol
    results = {}
    for symbol in tqdm(symbol_list):
        results[symbol] = calculate_sharpe(symbol)
    
    # Add risk metrics to dataframe
    df['Sharpe Ratio'] = df['Symbol'].apply(
        lambda s: results.get(s, {}).get('sharpe_ratio', np.nan) if results.get(s) else np.nan
    )
    df['Sortino Ratio'] = df['Symbol'].apply(
        lambda s: results.get(s, {}).get('sortino_ratio', np.nan) if results.get(s) else np.nan
    )
    df['Alpha'] = df['Symbol'].apply(
        lambda s: results.get(s, {}).get('alpha', np.nan) if results.get(s) else np.nan
    )
    df['Beta'] = df['Symbol'].apply(
        lambda s: results.get(s, {}).get('beta', np.nan) if results.get(s) else np.nan
    )
    
    # Filter out rows with missing risk metrics
    screened_df = df.dropna(subset=['Sharpe Ratio'])
    failed_symbols = [s for s in symbol_list if s not in screened_df['Symbol'].tolist()]
    
    # Sort by Sharpe Ratio (risk-adjusted return)
    screened_df = screened_df.sort_values(by='Sharpe Ratio', ascending=False)
    
    # Add logs for each stock
    for _, row in screened_df.iterrows():
        symbol = row['Symbol']
        logs.append(
            f"""\n{symbol} | Sharpe Ratio: {row['Sharpe Ratio']:.2f}, Sortino Ratio: {row['Sortino Ratio']:.2f}
            Alpha: {row['Alpha']*100:.2f}%, Beta: {row['Beta']:.2f}\n"""
        )
    
    # Serialize data in JSON format and save
    create_outfile(screened_df, "risk_adjusted_returns")
    
    # Mark iteration as complete
    mark_iteration_complete(iteration_name)
    
    # Print log
    print("".join(logs))
    
    # Record end time
    end = time.perf_counter()
    
    # Print footer
    cprint(f"{len(failed_symbols)} symbols failed (insufficient data for risk calculation).", "dark_grey")
    cprint(f"{len(screened_df)} symbols ranked by risk-adjusted returns.", "green")
    print_status(process_name, process_stage, False, end - start)
    print_divider()

# Update run_screen.py to include this iteration
# final_iteration = "risk_adjusted_returns"
```

## Summary of Enhancements

1. **Price Range Flexibility**: Allow users to select from predefined price ranges or create custom ranges via command-line arguments.

2. **Strategy Picker**: Implement different screening strategies (momentum, value-growth, breakout) with preset parameters for quick switching between investment styles.

3. **Performance Backtesting**: Add a backtesting module that analyzes how the screened stocks would have performed over a selected time period, comparing against a benchmark.

4. **Momentum Indicators**: Expand the technical analysis with momentum indicators (RSI, MACD, ADX) to provide more sophisticated trend analysis.

5. **Sharpe Ratio and Risk-Adjusted Returns**: Calculate risk-adjusted return metrics (Sharpe, Sortino, Alpha, Beta) to rank stocks not just by growth potential but also by risk-adjusted performance.

## Implementation Plan

1. **Phase 1**: Add command-line arguments for price range flexibility and strategy selection
2. **Phase 2**: Implement backtesting module for evaluating historical performance
3. **Phase 3**: Add momentum indicators and risk-adjusted return calculations
4. **Phase 4**: Create improved visualization and reporting capabilities
5. **Phase 5**: Optimize performance for larger stock datasets

These enhancements will transform the Growth Stock Screener into a more flexible, powerful tool capable of supporting different investment styles while adding quantitative validation through backtesting and risk-adjusted performance metrics.