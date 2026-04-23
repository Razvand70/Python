'''
SMT (Smart Money Technique) Divergence Detector
Pairs: EUR/USD vs GBP/USD

Requirements:
pip install yfinance pandas numpy

Usage:
python smt_divergence.py
'''

import yfinance as yf
import pandas as pd
import numpy as np

# ─────────────────────────────────────────────

# 1. DATA FETCHING

# ─────────────────────────────────────────────

def fetch_data(ticker: str, period: str = '60d', interval: str = '1h') -> pd.DataFrame:
'''Download OHLC data from Yahoo Finance.'''
df = yf.download(ticker, period=period, interval=interval, auto_adjust=True, progress=False)
df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df.columns]
df.index = pd.to_datetime(df.index)
return df[['open', 'high', 'low', 'close']]

# ─────────────────────────────────────────────

# 2. SWING HIGH / LOW DETECTION

# ─────────────────────────────────────────────

def find_swings(df: pd.DataFrame, lookback: int = 5) -> pd.DataFrame:
'''
Identify swing highs and swing lows.

```
A swing high: candle whose high is the highest in a window of
(lookback) candles on each side.
A swing low:  candle whose low  is the lowest  in a window of
(lookback) candles on each side.
'''
df = df.copy()
df["swing_high"] = np.nan
df["swing_low"] = np.nan

for i in range(lookback, len(df) - lookback):
    window_highs = df["high"].iloc[i - lookback: i + lookback + 1]
    window_lows  = df["low"].iloc[i - lookback: i + lookback + 1]

    if df["high"].iloc[i] == window_highs.max():
        df.at[df.index[i], "swing_high"] = df["high"].iloc[i]

    if df["low"].iloc[i] == window_lows.min():
        df.at[df.index[i], "swing_low"] = df["low"].iloc[i]

return df
```

# ─────────────────────────────────────────────

# 3. SMT DIVERGENCE DETECTION

# ─────────────────────────────────────────────

def detect_smt_divergence(
df_a: pd.DataFrame,
df_b: pd.DataFrame,
lookback: int = 5,
time_tolerance: int = 3,      # candles either side to match swing points
) -> pd.DataFrame:
'''
Detect SMT divergences between two correlated pairs.


Parameters
----------
df_a, df_b      : OHLC DataFrames (same timeframe)
lookback        : swing detection lookback
time_tolerance  : max candle offset to match a swing on both pairs

Returns
-------
DataFrame of divergence signals with columns:
    time, type, price_a, price_b, description
'''
df_a = find_swings(df_a, lookback)
df_b = find_swings(df_b, lookback)

# Align on common timestamps
common_idx = df_a.index.intersection(df_b.index)
df_a = df_a.loc[common_idx]
df_b = df_b.loc[common_idx]

signals = []

highs_a = df_a["swing_high"].dropna()
lows_a  = df_a["swing_low"].dropna()
highs_b = df_b["swing_high"].dropna()
lows_b  = df_b["swing_low"].dropna()

def nearby_swing(swing_series: pd.Series, ts: pd.Timestamp) -> float | None:
    """Return the nearest swing value within time_tolerance candles."""
    if ts not in common_idx:
        return None
    pos = common_idx.get_loc(ts)
    lo  = max(0, pos - time_tolerance)
    hi  = min(len(common_idx) - 1, pos + time_tolerance)
    window = swing_series[
        (swing_series.index >= common_idx[lo]) &
        (swing_series.index <= common_idx[hi])
    ]
    return window.iloc[0] if not window.empty else None

# ── Bearish SMT: A makes higher high, B makes lower high ──────────────
prev_high_a = prev_high_b = None
prev_ts_a  = prev_ts_b  = None

for ts, val in highs_a.items():
    match_b = nearby_swing(highs_b, ts)
    if match_b is None:
        continue

    if prev_high_a is not None and prev_high_b is not None:
        # A: higher high  |  B: lower high  → bearish divergence
        if val > prev_high_a and match_b < prev_high_b:
            signals.append({
                "time":        ts,
                "type":        "BEARISH SMT",
                "price_a":    round(val, 5),
                "price_b":    round(match_b, 5),
                "description": (
                    f"EUR/USD made a HIGHER high ({val:.5f} > {prev_high_a:.5f}) "
                    f"while GBP/USD made a LOWER high ({match_b:.5f} < {prev_high_b:.5f}). "
                    "Bearish reversal probable."
                ),
            })
        # Inverse: B higher high, A lower high
        elif match_b > prev_high_b and val < prev_high_a:
            signals.append({
                "time":        ts,
                "type":        "BEARISH SMT (inverse)",
                "price_a":    round(val, 5),
                "price_b":    round(match_b, 5),
                "description": (
                    f"GBP/USD made a HIGHER high ({match_b:.5f} > {prev_high_b:.5f}) "
                    f"while EUR/USD made a LOWER high ({val:.5f} < {prev_high_a:.5f}). "
                    "Bearish reversal probable."
                ),
            })

    prev_high_a, prev_ts_a = val,    ts
    prev_high_b, prev_ts_b = match_b, ts

# ── Bullish SMT: A makes lower low, B makes higher low ────────────────
prev_low_a = prev_low_b = None

for ts, val in lows_a.items():
    match_b = nearby_swing(lows_b, ts)
    if match_b is None:
        continue

    if prev_low_a is not None and prev_low_b is not None:
        # A: lower low  |  B: higher low  → bullish divergence
        if val < prev_low_a and match_b > prev_low_b:
            signals.append({
                "time":        ts,
                "type":        "BULLISH SMT",
                "price_a":    round(val, 5),
                "price_b":    round(match_b, 5),
                "description": (
                    f"EUR/USD made a LOWER low ({val:.5f} < {prev_low_a:.5f}) "
                    f"while GBP/USD made a HIGHER low ({match_b:.5f} > {prev_low_b:.5f}). "
                    "Bullish reversal probable."
                ),
            })
        # Inverse
        elif match_b < prev_low_b and val > prev_low_a:
            signals.append({
                "time":        ts,
                "type":        "BULLISH SMT (inverse)",
                "price_a":    round(val, 5),
                "price_b":    round(match_b, 5),
                "description": (
                    f"GBP/USD made a LOWER low ({match_b:.5f} < {prev_low_b:.5f}) "
                    f"while EUR/USD made a HIGHER low ({val:.5f} > {prev_low_a:.5f}). "
                    "Bullish reversal probable."
                ),
            })

    prev_low_a = val
    prev_low_b = match_b

result = pd.DataFrame(signals)
if not result.empty:
    result = result.sort_values("time").drop_duplicates(subset=["time", "type"])
    result = result.reset_index(drop=True)
return result
```

# ─────────────────────────────────────────────

# 4. MAIN

# ─────────────────────────────────────────────

def main():
PERIOD  = '60d'
INTERVAL = '1h'
LOOKBACK = 5      # swing detection sensitivity (candles)
TOLERANCE = 3      # max candle distance to match swings across pairs

```
print("Fetching EUR/USD data …")
eurusd = fetch_data("EURUSD=X", period=PERIOD, interval=INTERVAL)

print("Fetching GBP/USD data …")
gbpusd = fetch_data("GBPUSD=X", period=PERIOD, interval=INTERVAL)

print(f"\nEUR/USD: {len(eurusd)} candles  |  GBP/USD: {len(gbpusd)} candles")

print("\nDetecting SMT divergences …\n")
signals = detect_smt_divergence(
    eurusd, gbpusd,
    lookback=LOOKBACK,
    time_tolerance=TOLERANCE,
)

if signals.empty:
    print("No SMT divergences found in the selected period/timeframe.")
    print("Try increasing the period or adjusting lookback/tolerance parameters.")
    return

print(f"{'─'*70}")
print(f"  Found {len(signals)} SMT divergence signal(s)")
print(f"{'─'*70}\n")

for _, row in signals.iterrows():
    tag = "🔴" if "BEARISH" in row["type"] else "🟢"
    print(f"{tag}  [{row['time'].strftime('%Y-%m-%d %H:%M')}]  {row['type']}")
    print(f"  EUR/USD: {row['price_a']:.5f}  |  GBP/USD: {row['price_b']:.5f}")
    print(f"  {row['description']}")
    print()

# Optional: save to CSV
out_file = "smt_signals.csv"
signals.to_csv(out_file, index=False)
print(f"Signals saved to {out_file}")


if **name** == **main**:
main()
