import pandas as pd
import numpy as np

def calculate_skyrocket_score(symbol_data, info, historical_price_data):
    """
    Calculates a simplified Skyrocket Score based on available metrics.
    Score is out of 10.
    Returns score (int) and reason (str).
    """
    score = 0
    reasons = []
    symbol = symbol_data['Symbol'] # Get symbol for indexing historical data

    # 1. Revenue Growth (Max 2 points)
    revenue_growth = info.get('revenueGrowth', None)
    if revenue_growth is not None:
        try:
            revenue_growth_pct = float(revenue_growth) * 100
            if revenue_growth_pct > 30:
                score += 2
                reasons.append(f"Strong Revenue Growth ({revenue_growth_pct:.1f}%)")
            elif revenue_growth_pct > 15:
                score += 1
                reasons.append(f"Positive Revenue Growth ({revenue_growth_pct:.1f}%)")
        except (ValueError, TypeError):
            pass # Ignore if conversion fails

    # 2. Price Performance (Max 3 points) - Using 1-year return and distance from high
    year_return = None
    pct_from_high = None
    current_price = info.get('currentPrice', None) # Use current price from info if available

    # Check if historical_price_data is a valid DataFrame and contains 'Close' column
    if isinstance(historical_price_data, pd.DataFrame) and not historical_price_data.empty and 'Close' in historical_price_data.columns:
        price_data = historical_price_data['Close'].dropna()
        if len(price_data) > 0:
            # Use info's current price if available, otherwise fallback to latest historical
            if current_price is None:
                 current_price = price_data.iloc[-1]

            if current_price is not None: # Ensure we have a price
                try:
                    current_price_float = float(current_price)
                    year_ago_price = price_data.iloc[0]
                    if year_ago_price != 0: # Avoid division by zero
                        year_return = ((current_price_float / year_ago_price) - 1) * 100

                    high_52week = price_data.max()
                    if high_52week != 0: # Avoid division by zero
                        pct_from_high = ((current_price_float / high_52week) - 1) * 100
                except (ValueError, TypeError):
                     pass # Ignore if conversion fails

    if year_return is not None:
        if year_return > 100:
            score += 2
            reasons.append(f"Excellent 1Y Return ({year_return:.1f}%)")
        elif year_return > 30:
            score += 1
            reasons.append(f"Good 1Y Return ({year_return:.1f}%)")

    if pct_from_high is not None and pct_from_high > -25: # Closer to high is better momentum
        score += 1
        reasons.append(f"Near 52W High ({pct_from_high:.1f}%)")


    # 3. RS Rating (Max 2 points)
    rs_rating = symbol_data.get('RS', None)
    if rs_rating is not None:
        try:
            rs_rating_float = float(rs_rating)
            if rs_rating_float >= 90:
                score += 2
                reasons.append(f"High RS Rating ({rs_rating_float:.0f})")
            elif rs_rating_float >= 80:
                score += 1
                reasons.append(f"Good RS Rating ({rs_rating_float:.0f})")
        except (ValueError, TypeError):
            pass # Ignore if conversion fails

    # 4. Institutional Ownership (Max 1 point)
    # Use 'institutionsPercentHeld' as it seems more common in yfinance info
    inst_ownership = info.get('institutionsPercentHeld', None)
    if inst_ownership is not None:
        try:
            inst_ownership_pct = float(inst_ownership) * 100
            if inst_ownership_pct > 20:
                score += 1
                reasons.append(f"Institutional Interest ({inst_ownership_pct:.1f}%)")
        except (ValueError, TypeError):
            pass # Ignore if conversion fails

    # 5. Trend (SMA) (Max 2 points)
    sma_50 = None
    sma_200 = None
    # Check again if historical_price_data is valid and contains 'Close'
    if isinstance(historical_price_data, pd.DataFrame) and not historical_price_data.empty and 'Close' in historical_price_data.columns:
         price_data = historical_price_data['Close'].dropna()
         if len(price_data) >= 50:
             sma_50 = price_data.rolling(window=50).mean().iloc[-1]
         if len(price_data) >= 200:
             sma_200 = price_data.rolling(window=200).mean().iloc[-1]

    if current_price is not None and sma_50 is not None:
        try:
            if float(current_price) > sma_50:
                score += 1
                reasons.append("Price > 50-day SMA")
        except (ValueError, TypeError):
            pass
    if current_price is not None and sma_200 is not None:
        try:
            if float(current_price) > sma_200:
                score += 1
                reasons.append("Price > 200-day SMA")
        except (ValueError, TypeError):
            pass


    # Normalize score to be out of 10 (Max possible score is 10)
    final_score = min(score, 10)

    return final_score, ", ".join(reasons) if reasons else "N/A"


def generate_top_10_html(scored_df):
    """
    Generates the HTML snippet for the Top 10 Skyrocket Candidates.
    """
    if 'Skyrocket Score' not in scored_df.columns or scored_df.empty:
        return ""

    # Ensure score is numeric before sorting
    scored_df['Skyrocket Score'] = pd.to_numeric(scored_df['Skyrocket Score'], errors='coerce')
    scored_df = scored_df.dropna(subset=['Skyrocket Score'])

    top_10 = scored_df.nlargest(10, 'Skyrocket Score')

    if top_10.empty:
        return """
        <div class="skyrocket-summary">
             <h2>Top 10 Skyrocket Candidates</h2>
             <p>No stocks met the criteria for Skyrocket Candidates based on the current scoring.</p>
        </div>
        <hr>
        """

    html = """
    <div class="skyrocket-summary">
        <h2>Top 10 Skyrocket Candidates</h2>
        <ol>
    """
    for index, row in top_10.iterrows():
        symbol = row['Symbol']
        # Ensure score is displayed as an integer
        score = int(row['Skyrocket Score']) if pd.notna(row['Skyrocket Score']) else 'N/A'
        reason = row['Skyrocket Reason'] if pd.notna(row['Skyrocket Reason']) else 'N/A'
        html += f"""
            <li>
                <strong>{symbol} (Score: {score}/10)</strong>: {reason}
            </li>
        """

    html += """
        </ol>
        <p><small>Note: Skyrocket Score is a simplified calculation based on growth, performance, RS rating, institutional interest, and trend.</small></p>
    </div>
    <hr>
    """
    return html