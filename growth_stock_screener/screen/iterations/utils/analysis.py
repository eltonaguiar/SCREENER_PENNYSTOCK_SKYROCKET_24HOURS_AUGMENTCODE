import os
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
from termcolor import colored
import requests
import json
from .outfiles import open_outfile
from .skyrocket import calculate_skyrocket_score, generate_top_10_html # Import new functions

def analyze_symbols():
    """
    Create a detailed analysis of the symbols that passed all screening stages.
    Includes:
    - Price performance metrics
    - Growth metrics
    - Technical indicators
    - Industry comparisons
    """
    print(colored("\nAnalyzing final symbols...", "light_green"))

    # Load the final results
    try:
        df = open_outfile("institutional_accumulation")
        if len(df) == 0:
            print(colored("No symbols passed all screening stages.", "yellow"))
            return None
    except Exception as e:
        print(colored(f"Error loading final results: {e}", "red"))
        return None

    # Create a directory for the analysis if it doesn't exist
    analysis_dir = os.path.join(os.getcwd(), "analysis")
    if not os.path.exists(analysis_dir):
        os.makedirs(analysis_dir)

    # Get the current date for the filename
    time_string = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    analysis_file = os.path.join(analysis_dir, f"symbols_analysis_{time_string}.html")

    # Start building the HTML content
    html_content = []
    html_content.append("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Stock Analysis Report</title>
        <style>
            /* General Styles */
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                color: #333;
            }
            h1, h2, h3 {
                color: #2c3e50;
            }
            .header {
                background-color: #3498db;
                color: white;
                padding: 20px;
                text-align: center;
                margin-bottom: 30px;
                border-radius: 5px;
            }
            .summary {
                background-color: #f9f9f9;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
                border-left: 5px solid #3498db;
            }
            /* Skyrocket Summary Styles */
            .skyrocket-summary {
                background-color: #eaf5ff; /* Light blue background */
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
                border-left: 5px solid #2980b9; /* Darker blue border */
            }
            .skyrocket-summary h2 {
                margin-top: 0;
                color: #2c3e50;
            }
            .skyrocket-summary ol {
                list-style-position: inside;
                padding-left: 10px; /* Indent list */
            }
            .skyrocket-summary li {
                margin-bottom: 0.8em;
                padding: 0.4em 0;
                border-left: none; /* Remove individual item border */
                background-color: transparent; /* No background for items */
            }
            .skyrocket-summary strong {
                color: #0056b3;
            }
            .skyrocket-summary p small {
                color: #7f8c8d;
                font-style: italic;
            }
            /* Stock Card Styles */
            .stock-card {
                background-color: #fff;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .stock-header {
                display: flex;
                justify-content: space-between;
                border-bottom: 1px solid #eee;
                padding-bottom: 10px;
                margin-bottom: 15px;
            }
            .stock-name {
                font-size: 24px;
                font-weight: bold;
            }
            .stock-price {
                font-size: 24px;
                color: #27ae60;
            }
            .metrics {
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                margin-bottom: 20px;
            }
            .metric-group {
                flex: 1;
                min-width: 250px;
            }
            .metric {
                margin-bottom: 10px;
            }
            .metric-label {
                font-weight: bold;
                color: #7f8c8d;
            }
            .metric-value {
                font-weight: bold;
            }
            .positive {
                color: #27ae60;
            }
            .negative {
                color: #e74c3c;
            }
            .neutral {
                color: #3498db;
            }
            .chart-container {
                margin-top: 20px;
                text-align: center;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }
            th, td {
                padding: 12px 15px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #f2f2f2;
                font-weight: bold;
            }
            tr:hover {
                background-color: #f5f5f5;
            }
            .footer {
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #eee;
                color: #7f8c8d;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Stock Analysis Report</h1>
            <p>Stocks Under $4 with High Growth Potential</p>
            <p>Generated on """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
        </div>

        <div class="summary">
            <h2>Analysis Summary</h2>
            <p>This report analyzes """ + str(len(df)) + """ stocks that passed all screening criteria.</p>
            <p>These stocks have been filtered for:</p>
            <ul>
                <li>Price under $4</li>
                <li>Strong relative strength (RS rating >= 80)</li>
                <li>Sufficient liquidity (minimum volume and market cap)</li>
                <li>Positive revenue growth trends</li>
                <li>Institutional accumulation</li>
            </ul>
        </div>

        <!-- Placeholder for Skyrocket Summary - will be added dynamically -->

        <h2>Detailed Stock Analysis</h2>
    """)

    # Get detailed data for each symbol
    symbols = df['Symbol'].tolist()

    # Add columns for Skyrocket Score and Reason
    df['Skyrocket Score'] = np.nan
    df['Skyrocket Reason'] = ''

    # Fetch data for all symbols at once
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    try:
        # Get historical data for the past year
        historical_data = yf.download(symbols, start=start_date, end=end_date)

        # Get more detailed info for each symbol
        for symbol in symbols:
            try:
                print(colored(f"Analyzing {symbol}...", "cyan"))

                # Get the row for this symbol from our screened data
                symbol_row = df[df['Symbol'] == symbol].iloc[0]

                # Get additional data from Yahoo Finance
                ticker = yf.Ticker(symbol)
                info = ticker.info

                # Extract relevant information
                company_name = symbol_row.get('Company Name', info.get('longName', symbol))
                current_price = symbol_row.get('Price', info.get('currentPrice', 'N/A'))
                market_cap = symbol_row.get('Market Cap', info.get('marketCap', 'N/A'))
                industry = symbol_row.get('Industry', info.get('industry', 'N/A'))
                rs_rating = symbol_row.get('RS', 'N/A')

                # Format market cap
                if isinstance(market_cap, (int, float)):
                    if market_cap >= 1e9:
                        market_cap_str = f"${market_cap/1e9:.2f}B"
                    elif market_cap >= 1e6:
                        market_cap_str = f"${market_cap/1e6:.2f}M"
                    else:
                        market_cap_str = f"${market_cap:.2f}"
                else:
                    market_cap_str = str(market_cap)

                # Calculate performance metrics
                try:
                    # Get price data for this symbol
                    price_data = historical_data['Close'][symbol].dropna()

                    if len(price_data) > 0:
                        # Calculate returns
                        current_price = price_data.iloc[-1]
                        week_ago_price = price_data.iloc[-5] if len(price_data) >= 5 else price_data.iloc[0]
                        month_ago_price = price_data.iloc[-20] if len(price_data) >= 20 else price_data.iloc[0]
                        three_month_ago_price = price_data.iloc[-60] if len(price_data) >= 60 else price_data.iloc[0]
                        six_month_ago_price = price_data.iloc[-120] if len(price_data) >= 120 else price_data.iloc[0]
                        year_ago_price = price_data.iloc[0]

                        week_return = ((current_price / week_ago_price) - 1) * 100
                        month_return = ((current_price / month_ago_price) - 1) * 100
                        three_month_return = ((current_price / three_month_ago_price) - 1) * 100
                        six_month_return = ((current_price / six_month_ago_price) - 1) * 100
                        year_return = ((current_price / year_ago_price) - 1) * 100

                        # Calculate volatility (standard deviation of daily returns)
                        daily_returns = price_data.pct_change().dropna()
                        volatility = daily_returns.std() * 100

                        # Calculate 50-day and 200-day moving averages
                        sma_50 = price_data.rolling(window=50).mean().iloc[-1] if len(price_data) >= 50 else None
                        sma_200 = price_data.rolling(window=200).mean().iloc[-1] if len(price_data) >= 200 else None

                        # Calculate distance from 52-week high and low
                        high_52week = price_data.max()
                        low_52week = price_data.min()
                        pct_from_high = ((current_price / high_52week) - 1) * 100
                        pct_from_low = ((current_price / low_52week) - 1) * 100

                        # Calculate RSI (14-day)
                        delta = price_data.diff()
                        gain = delta.clip(lower=0)
                        loss = -delta.clip(upper=0)
                        avg_gain = gain.rolling(window=14).mean()
                        avg_loss = loss.rolling(window=14).mean()
                        rs = avg_gain / avg_loss
                        rsi = 100 - (100 / (1 + rs))
                        current_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else None
                    else:
                        week_return = month_return = three_month_return = six_month_return = year_return = None
                        volatility = None
                        sma_50 = sma_200 = None
                        high_52week = low_52week = None
                        pct_from_high = pct_from_low = None
                        current_rsi = None
                except Exception as e:
                    print(colored(f"Error calculating metrics for {symbol}: {e}", "yellow"))
                    week_return = month_return = three_month_return = six_month_return = year_return = None
                    volatility = None
                    sma_50 = sma_200 = None
                    high_52week = low_52week = None
                    pct_from_high = pct_from_low = None
                    current_rsi = None

                # Get additional financial metrics
                try:
                    # Try to get revenue growth
                    revenue_growth = info.get('revenueGrowth', None)
                    if revenue_growth is not None:
                        revenue_growth = revenue_growth * 100

                    # Try to get earnings growth
                    earnings_growth = info.get('earningsGrowth', None)
                    if earnings_growth is not None:
                        earnings_growth = earnings_growth * 100

                    # Get other metrics
                    pe_ratio = info.get('trailingPE', None)
                    forward_pe = info.get('forwardPE', None)
                    peg_ratio = info.get('pegRatio', None)
                    profit_margins = info.get('profitMargins', None)
                    if profit_margins is not None:
                        profit_margins = profit_margins * 100

                    # Get institutional ownership
                    inst_ownership = info.get('institutionalOwnershipPercentage', None)
                    if inst_ownership is None:
                        inst_ownership = info.get('institutionsPercentHeld', None)
                    if inst_ownership is not None:
                        inst_ownership = inst_ownership * 100

                    # Get analyst recommendations
                    target_price = info.get('targetMeanPrice', None)
                    target_high = info.get('targetHighPrice', None)
                    target_low = info.get('targetLowPrice', None)

                    if target_price is not None and current_price is not None:
                        upside_potential = ((target_price / current_price) - 1) * 100
                    else:
                        upside_potential = None

                except Exception as e:
                    print(colored(f"Error getting financial metrics for {symbol}: {e}", "yellow"))
                    revenue_growth = earnings_growth = pe_ratio = forward_pe = peg_ratio = profit_margins = None
                    inst_ownership = target_price = target_high = target_low = upside_potential = None

                # Calculate Skyrocket Score
                try:
                    # Pass the relevant parts of historical_data
                    symbol_historical_data = None
                    if historical_data is not None and not historical_data.empty:
                        # Check if multi-level index (multiple symbols) or single
                        if isinstance(historical_data.columns, pd.MultiIndex):
                            if symbol in historical_data.columns.get_level_values(1):
                                symbol_historical_data = historical_data.loc[:, pd.IndexSlice[:, symbol]]
                                # Rename columns to remove symbol level for consistency
                                symbol_historical_data.columns = symbol_historical_data.columns.droplevel(1)
                        elif symbol in historical_data.columns: # Single symbol case (less likely here)
                            symbol_historical_data = historical_data

                    score, reason = calculate_skyrocket_score(symbol_row, info, symbol_historical_data)
                    df.loc[df['Symbol'] == symbol, 'Skyrocket Score'] = score
                    df.loc[df['Symbol'] == symbol, 'Skyrocket Reason'] = reason
                except Exception as score_e:
                    print(colored(f"Error calculating Skyrocket Score for {symbol}: {score_e}", "yellow"))
                    df.loc[df['Symbol'] == symbol, 'Skyrocket Score'] = 0
                    df.loc[df['Symbol'] == symbol, 'Skyrocket Reason'] = "Error during scoring"

                # Create the HTML for this stock
                # Format the current price
                if isinstance(current_price, (int, float)):
                    price_display = f"${current_price:.2f}"
                else:
                    price_display = f"${current_price}"

                stock_html = f"""
                <div class="stock-card">
                    <div class="stock-header">
                        <div class="stock-name">{symbol}: {company_name}</div>
                        <div class="stock-price">{price_display}</div>
                    </div>

                    <div class="metrics">
                        <div class="metric-group">
                            <h3>Company Information</h3>
                            <div class="metric">
                                <span class="metric-label">Industry:</span>
                                <span class="metric-value">{industry}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Market Cap:</span>
                                <span class="metric-value">{market_cap_str}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">RS Rating:</span>
                                <span class="metric-value">{rs_rating}</span>
                            </div>
                        </div>

                        <div class="metric-group">
                            <h3>Performance</h3>
                """

                # Add performance metrics if available
                if week_return is not None:
                    stock_html += f"""
                            <div class="metric">
                                <span class="metric-label">1 Week:</span>
                                <span class="metric-value {'positive' if week_return > 0 else 'negative'}">{week_return:.2f}%</span>
                            </div>
                    """

                if month_return is not None:
                    stock_html += f"""
                            <div class="metric">
                                <span class="metric-label">1 Month:</span>
                                <span class="metric-value {'positive' if month_return > 0 else 'negative'}">{month_return:.2f}%</span>
                            </div>
                    """

                if three_month_return is not None:
                    stock_html += f"""
                            <div class="metric">
                                <span class="metric-label">3 Months:</span>
                                <span class="metric-value {'positive' if three_month_return > 0 else 'negative'}">{three_month_return:.2f}%</span>
                            </div>
                    """

                if six_month_return is not None:
                    stock_html += f"""
                            <div class="metric">
                                <span class="metric-label">6 Months:</span>
                                <span class="metric-value {'positive' if six_month_return > 0 else 'negative'}">{six_month_return:.2f}%</span>
                            </div>
                    """

                if year_return is not None:
                    stock_html += f"""
                            <div class="metric">
                                <span class="metric-label">1 Year:</span>
                                <span class="metric-value {'positive' if year_return > 0 else 'negative'}">{year_return:.2f}%</span>
                            </div>
                    """

                stock_html += """
                        </div>

                        <div class="metric-group">
                            <h3>Technical Indicators</h3>
                """

                # Add technical indicators if available
                if volatility is not None:
                    stock_html += f"""
                            <div class="metric">
                                <span class="metric-label">Volatility (Daily):</span>
                                <span class="metric-value">{volatility:.2f}%</span>
                            </div>
                    """

                if current_rsi is not None:
                    rsi_class = "neutral"
                    if current_rsi > 70:
                        rsi_class = "negative"  # Overbought
                    elif current_rsi < 30:
                        rsi_class = "positive"  # Oversold

                    stock_html += f"""
                            <div class="metric">
                                <span class="metric-label">RSI (14-day):</span>
                                <span class="metric-value {rsi_class}">{current_rsi:.2f}</span>
                            </div>
                    """

                if sma_50 is not None and current_price is not None:
                    pct_from_sma50 = ((current_price / sma_50) - 1) * 100
                    stock_html += f"""
                            <div class="metric">
                                <span class="metric-label">50-day SMA:</span>
                                <span class="metric-value">${sma_50:.2f} ({pct_from_sma50:.2f}%)</span>
                            </div>
                    """

                if sma_200 is not None and current_price is not None:
                    pct_from_sma200 = ((current_price / sma_200) - 1) * 100
                    stock_html += f"""
                            <div class="metric">
                                <span class="metric-label">200-day SMA:</span>
                                <span class="metric-value">${sma_200:.2f} ({pct_from_sma200:.2f}%)</span>
                            </div>
                    """

                if pct_from_high is not None:
                    stock_html += f"""
                            <div class="metric">
                                <span class="metric-label">From 52-week High:</span>
                                <span class="metric-value negative">{pct_from_high:.2f}%</span>
                            </div>
                    """

                if pct_from_low is not None:
                    stock_html += f"""
                            <div class="metric">
                                <span class="metric-label">From 52-week Low:</span>
                                <span class="metric-value positive">+{pct_from_low:.2f}%</span>
                            </div>
                    """

                stock_html += """
                        </div>

                        <div class="metric-group">
                            <h3>Growth & Valuation</h3>
                """

                # Add growth and valuation metrics if available
                if revenue_growth is not None:
                    stock_html += f"""
                            <div class="metric">
                                <span class="metric-label">Revenue Growth:</span>
                                <span class="metric-value {'positive' if revenue_growth > 0 else 'negative'}">{revenue_growth:.2f}%</span>
                            </div>
                    """

                if earnings_growth is not None:
                    stock_html += f"""
                            <div class="metric">
                                <span class="metric-label">Earnings Growth:</span>
                                <span class="metric-value {'positive' if earnings_growth > 0 else 'negative'}">{earnings_growth:.2f}%</span>
                            </div>
                    """

                if pe_ratio is not None:
                    stock_html += f"""
                            <div class="metric">
                                <span class="metric-label">P/E Ratio:</span>
                                <span class="metric-value">{pe_ratio:.2f}</span>
                            </div>
                    """

                if forward_pe is not None:
                    stock_html += f"""
                            <div class="metric">
                                <span class="metric-label">Forward P/E:</span>
                                <span class="metric-value">{forward_pe:.2f}</span>
                            </div>
                    """

                if peg_ratio is not None:
                    stock_html += f"""
                            <div class="metric">
                                <span class="metric-label">PEG Ratio:</span>
                                <span class="metric-value">{peg_ratio:.2f}</span>
                            </div>
                    """

                if profit_margins is not None:
                    stock_html += f"""
                            <div class="metric">
                                <span class="metric-label">Profit Margin:</span>
                                <span class="metric-value {'positive' if profit_margins > 0 else 'negative'}">{profit_margins:.2f}%</span>
                            </div>
                    """

                stock_html += """
                        </div>

                        <div class="metric-group">
                            <h3>Analyst Opinions</h3>
                """

                # Add analyst opinions if available
                if inst_ownership is not None:
                    stock_html += f"""
                            <div class="metric">
                                <span class="metric-label">Institutional Ownership:</span>
                                <span class="metric-value">{inst_ownership:.2f}%</span>
                            </div>
                    """

                if target_price is not None:
                    stock_html += f"""
                            <div class="metric">
                                <span class="metric-label">Target Price:</span>
                                <span class="metric-value">${target_price:.2f}</span>
                            </div>
                    """

                if upside_potential is not None:
                    stock_html += f"""
                            <div class="metric">
                                <span class="metric-label">Upside Potential:</span>
                                <span class="metric-value {'positive' if upside_potential > 0 else 'negative'}">{upside_potential:.2f}%</span>
                            </div>
                    """

                if target_high is not None:
                    stock_html += f"""
                            <div class="metric">
                                <span class="metric-label">Target High:</span>
                                <span class="metric-value">${target_high:.2f}</span>
                            </div>
                    """

                if target_low is not None:
                    stock_html += f"""
                            <div class="metric">
                                <span class="metric-label">Target Low:</span>
                                <span class="metric-value">${target_low:.2f}</span>
                            </div>
                    """

                stock_html += """
                        </div>
                    </div>

                    <div class="chart-container">
                        <h3>Price Chart (1 Year)</h3>
                        <p>Visit <a href="https://finance.yahoo.com/quote/""" + symbol + """" target="_blank">Yahoo Finance</a> for interactive charts.</p>
                    </div>

                    <div class="investment-thesis">
                        <h3>Investment Thesis</h3>
                        <p>""" + symbol + """ is a potential growth stock trading under $4 with the following characteristics:</p>
                        <ul>
                """

                # Add bullet points based on available metrics
                if rs_rating is not None and isinstance(rs_rating, (int, float)) and rs_rating >= 80:
                    stock_html += f"""
                            <li>Strong relative strength with an RS rating of {rs_rating}</li>
                    """

                if revenue_growth is not None and revenue_growth > 20:
                    stock_html += f"""
                            <li>Impressive revenue growth of {revenue_growth:.2f}%</li>
                    """

                if earnings_growth is not None and earnings_growth > 0:
                    stock_html += f"""
                            <li>Positive earnings growth of {earnings_growth:.2f}%</li>
                    """

                if inst_ownership is not None and inst_ownership > 15:
                    stock_html += f"""
                            <li>Significant institutional ownership of {inst_ownership:.2f}%</li>
                    """

                if upside_potential is not None and upside_potential > 20:
                    stock_html += f"""
                            <li>Strong upside potential of {upside_potential:.2f}% based on analyst targets</li>
                    """

                if current_price is not None and sma_50 is not None and current_price > sma_50:
                    stock_html += """
                            <li>Trading above its 50-day moving average, showing positive momentum</li>
                    """

                if pct_from_high is not None and pct_from_high > -30:
                    stock_html += f"""
                            <li>Within {abs(pct_from_high):.2f}% of its 52-week high</li>
                    """

                stock_html += """
                        </ul>
                        <p><strong>Note:</strong> This is an automated analysis based on screening criteria. Always conduct your own research before investing.</p>
                    </div>
                </div>
                """

                html_content.append(stock_html)

            except Exception as e:
                print(colored(f"Error analyzing {symbol}: {e}", "red"))
                continue

        # Generate and Insert Top 10 Skyrocket HTML after the loop
        try:
            top_10_html = generate_top_10_html(df)
            # Find the index of the initial summary div closing tag in html_content
            summary_end_index = -1
            for i, content in enumerate(html_content):
                if '</div>' in content and '<div class="summary">' in html_content[i-1] if i > 0 else False: # A bit fragile, assumes structure
                    summary_end_index = i
                    break
                # More robust check if the above fails
                if '<!-- Placeholder for Skyrocket Summary -->' in content:
                    summary_end_index = i
                    break

            if summary_end_index != -1:
                # Insert the top_10_html after the summary div
                html_content.insert(summary_end_index + 1, top_10_html)
                # Remove the placeholder comment if it exists
                html_content = [line for line in html_content if '<!-- Placeholder for Skyrocket Summary -->' not in line]

            else:
                # Fallback: Insert before the "Detailed Stock Analysis" header if placeholder not found
                for i, content in enumerate(html_content):
                    if '<h2>Detailed Stock Analysis</h2>' in content:
                        html_content.insert(i, top_10_html)
                        break
                else: # If header not found either, append before footer
                     html_content.insert(-1, top_10_html) # Insert before the last element (footer)

        except Exception as top10_e:
            print(colored(f"Error generating Top 10 Skyrocket HTML: {top10_e}", "red"))

        # Add the footer and close the HTML
        html_content.append("""
        <div class="footer">
            <p>Generated by Growth Stock Screener</p>
            <p>This report is for informational purposes only and does not constitute investment advice.</p>
        </div>
    </body>
    </html>
        """)

        # Write the HTML to a file
        with open(analysis_file, 'w') as f:
            f.write(''.join(html_content))

        print(colored(f"\nSymbols analysis completed and saved to: {analysis_file}", "green"))
        return analysis_file

    except Exception as e:
        print(colored(f"Error during symbols analysis: {e}", "red"))
        return None
