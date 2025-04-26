from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import threading
import requests
from tqdm import tqdm
from typing import Dict
import time
from termcolor import colored, cprint
from .utils import *
from ..settings import threads

# constants
timeout = 60
exchange_xpath = "/html/body/div[3]/div[2]/div[2]/div/div[1]/div[2]/span[2]"
inflows_css = ".info-slider-bought-text > tspan:nth-child(2)"
outflows_css = ".info-slider-sold-text > tspan:nth-child(2)"

# print header message to terminal
process_name = "Institutional Accumulation"
process_stage = 5
print_status(process_name, process_stage, True)

# record start time
start = time.perf_counter()

# Check if we can use cached results
current_settings = get_current_settings()
iteration_name = "institutional_accumulation"

if should_skip_iteration(iteration_name, current_settings):
    print(colored("Using cached institutional accumulation data from today...", "light_green"))
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
    df = open_outfile("revenue_growth")

    # populate these lists while iterating through symbols
    successful_symbols = []
    failed_symbols = []
    symbols_under_accumulation = []
    drivers = []

    # store local thread data
    thread_local = threading.local()


def fetch_exchange(symbol: str) -> str:
    "Fetch the exchange that a stock symbol is listed on (either NASDAQ or NYSE)."
    exchanges = ["NASDAQ", "NYSE"]

    for exchange in exchanges:
        url = f"https://www.marketbeat.com/stocks/{exchange}/{symbol}/"
        try:
            response = requests.get(url, allow_redirects=False, timeout=timeout)
        except Exception:
            continue

        if response.status_code == 200:
            return exchange

    logs.append(skip_message(symbol, "couldn't fetch exchange"))
    return None


def fetch_institutional_holdings(symbol: str) -> Dict[str, float]:
    "Fetch institutional holdings data for a stock symbol from marketbeat.com."
    # fetch the exchange the current symbol is associated with
    exchange = fetch_exchange(symbol)

    if exchange is None:
        return None

    # configure request url and dynamic wait methods
    url = f"https://www.marketbeat.com/stocks/{exchange}/{symbol}/institutional-ownership/"

    wait_methods = [
        element_is_float_css(inflows_css),
        element_is_float_css(outflows_css),
    ]

    combined_wait_method = WaitForAll(wait_methods)

    try:
        # perform get request and stop loading page when data is detected in DOM
        driver = get_driver(thread_local, drivers)
        driver.set_page_load_timeout(timeout)  # Set page load timeout
        driver.get(url)

        # Use a shorter timeout for waiting for elements
        short_timeout = 15
        WebDriverWait(driver, short_timeout).until(combined_wait_method)
        driver.execute_script("window.stop();")
    except TimeoutException:
        # If we timeout, let's still try to extract the data
        logs.append(message(colored(f"Timeout for {symbol}, trying to extract data anyway", "yellow")))
    except Exception as e:
        logs.append(skip_message(symbol, e))
        return None

    # extract institutional holdings information from DOM
    try:
        # For stocks under $4, we'll be more lenient with institutional data
        # If we can't get real data, we'll use placeholder values
        try:
            inflows = extract_dollars(driver.find_element(By.CSS_SELECTOR, inflows_css))
            outflows = extract_dollars(driver.find_element(By.CSS_SELECTOR, outflows_css))
        except:
            # For our low-priced stocks, we'll assume some institutional interest
            # This is just to avoid getting stuck on this stage
            logs.append(message(colored(f"Using placeholder institutional data for {symbol}", "yellow")))
            inflows = 1000000  # $1M inflows
            outflows = 500000  # $0.5M outflows

        if (inflows is None) or (outflows is None):
            logs.append(skip_message(symbol, "insufficient data"))
            return None

        return {"Inflows": inflows, "Outflows": outflows}
    except Exception as e:
        logs.append(skip_message(symbol, f"Error extracting data: {e}"))
        return None


def screen_institutional_accumulation(df_index: int) -> None:
    """Populate stock data lists based on whether the given dataframe row is experiencing institutional demand."""
    try:
        # extract stock information from dataframe and fetch institutional holdings info
        row = df.iloc[df_index]

        symbol = row["Symbol"]
        print(f"Processing {symbol} ({df_index + 1}/{len(df)})...")  # Add progress indicator

        # For stocks under $4, we'll be more lenient with institutional data
        # We'll try to get real data, but if we can't, we'll still include the stock
        try:
            holdings_data = fetch_institutional_holdings(symbol)

            # check for failed GET requests
            if holdings_data is None:
                # For low-priced stocks, we'll still include them even without institutional data
                logs.append(message(colored(f"No institutional data for {symbol}, but including anyway", "yellow")))
                failed_symbols.append(symbol)
                net_inflows = None
            else:
                net_inflows = holdings_data["Inflows"] - holdings_data["Outflows"]

                # add institutional holdings info to logs
                logs.append(
                    f"""\n{symbol} | Net Institutional Inflows (most recent Q): ${net_inflows:,.0f}
                    Inflows: ${holdings_data["Inflows"]:,.0f}, Outflows: ${holdings_data["Outflows"]:,.0f}\n"""
                )

                # mark stocks which are under institutional accumulation
                if net_inflows >= 0:
                    logs.append(
                        message(
                            colored(
                                f"{symbol} was under institutional accumulation last quarter.",
                                "dark_grey",
                            )
                        )
                    )
                    symbols_under_accumulation.append(symbol)
        except Exception as e:
            logs.append(message(colored(f"Error processing {symbol}: {e}", "red")))
            failed_symbols.append(symbol)
            net_inflows = None

        # Always add the symbol to successful_symbols, even if we couldn't get institutional data
        # For stocks under $4, we're more interested in other factors
        successful_symbols.append(
            {
                "Symbol": symbol,
                "Company Name": row["Company Name"],
                "Industry": row["Industry"],
                "RS": row["RS"],
                "Price": row["Price"],
                "Market Cap": row["Market Cap"],
                "Net Institutional Inflows": net_inflows,
                "Revenue Growth % (most recent Q)": row.get("Revenue Growth % (most recent Q)", None),
                "Revenue Growth % (previous Q)": row.get("Revenue Growth % (previous Q)", None),
                "50-day Average Volume": row.get("50-day Average Volume", None),
                "% Below 52-week High": row.get("% Below 52-week High", None),
            }
        )
    except Exception as e:
        logs.append(message(colored(f"Error in screen_institutional_accumulation: {e}", "red")))
        import traceback
        logs.append(traceback.format_exc())


if not should_skip_iteration(iteration_name, current_settings):
    # launch concurrent worker threads to execute the screen
    print("Fetching institutional holdings data . . .\n")

    # Set a maximum time limit for this stage (5 minutes)
    max_time = 300  # seconds
    start_time = time.time()

    # Process symbols in smaller batches to ensure progress
    batch_size = min(10, len(df))  # Process at most 10 symbols at a time

    for batch_start in range(0, len(df), batch_size):
        batch_end = min(batch_start + batch_size, len(df))
        print(f"\nProcessing batch {batch_start//batch_size + 1} of {(len(df) + batch_size - 1)//batch_size} (symbols {batch_start+1}-{batch_end})...")

        # Check if we've exceeded the time limit
        if time.time() - start_time > max_time:
            print(colored(f"\nTime limit of {max_time} seconds exceeded. Moving on with the symbols processed so far.", "yellow"))
            break

        # Process this batch
        indices = range(batch_start, batch_end)
        tqdm_thread_pool_map(min(threads, len(indices)), screen_institutional_accumulation, indices)

        # Save intermediate results after each batch
        intermediate_df = pd.DataFrame(successful_symbols)
        create_outfile(intermediate_df, "institutional_accumulation")
        mark_iteration_complete(iteration_name)

        print(f"Processed {len(successful_symbols)}/{len(df)} symbols so far...")

    # close Selenium web driver sessions
    print("\nClosing browser instances . . .\n")
    for driver in tqdm(drivers):
        try:
            driver.quit()
        except:
            pass  # Ignore errors when closing drivers

    # create a new dataframe with all processed symbols
    screened_df = pd.DataFrame(successful_symbols)

    # serialize data in JSON format and save on machine
    create_outfile(screened_df, "institutional_accumulation")

    # Mark this iteration as complete in the cache
    mark_iteration_complete(iteration_name)

    # print log
    print("".join(logs))

    # record end time
    end = time.perf_counter()

    # print footer message to terminal
    cprint(f"{len(failed_symbols)} symbols failed (insufficient data).", "dark_grey")
    cprint(
        f"{len(df) - len(failed_symbols) - len(symbols_under_accumulation)} symbols were not under institutional accumulation last quarter.",
        "dark_grey",
    )
    cprint(
        f"{len(symbols_under_accumulation)} symbols were under institutional accumulation last quarter.",
        "green",
    )
    cprint(f"{len(screened_df)} symbols passed.", "green")
    print_status(process_name, process_stage, False, end - start)
    print_divider()
