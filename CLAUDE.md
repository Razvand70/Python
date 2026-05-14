# CLAUDE.md

## Project Overview

This is a single-file Python script that detects **SMT (Smart Money Technique) divergences** between two correlated forex pairs — EUR/USD and GBP/USD. It fetches OHLC data from Yahoo Finance, identifies swing highs/lows, compares them across both pairs, and emits bullish/bearish reversal signals.

## Repository Structure

```
/
├── smt.py          # Entire application — data fetch, swing detection, divergence logic, CLI entry point
└── CLAUDE.md       # This file
```

There are no subdirectories, no tests, no CI/CD configuration, and no packaging files.

## Dependencies

Not tracked in a requirements file. Install manually:

```bash
pip install yfinance pandas numpy
```

| Package   | Role                                      |
|-----------|-------------------------------------------|
| yfinance  | Downloads OHLC candle data from Yahoo Finance |
| pandas    | DataFrame manipulation, time-series alignment |
| numpy     | NaN handling for swing point arrays       |

## Running the Script

```bash
python smt.py
```

Output is printed to stdout. Detected signals are also saved to `smt_signals.csv` in the working directory.

## Code Structure — `smt.py`

The file is divided into four numbered sections separated by visual dividers:

### 1. `fetch_data(ticker, period, interval)` — lines 22–27
Downloads OHLC data for a given Yahoo Finance ticker symbol. Normalises column names to lowercase. Returns a DataFrame with columns `open`, `high`, `low`, `close`.

### 2. `find_swings(df, lookback)` — lines 35–59
Scans a DataFrame and marks swing highs (local high over a symmetric `lookback`-candle window) and swing lows (local low) into new columns `swing_high` and `swing_low`. Non-swing rows are `NaN`.

### 3. `detect_smt_divergence(df_a, df_b, lookback, time_tolerance)` — lines 68–200
Core divergence logic:
- Calls `find_swings` on both DataFrames.
- Aligns them on a common timestamp index.
- Iterates over swing highs and lows on pair A, looks for a matching swing on pair B within `time_tolerance` candles.
- Emits four signal types: `BEARISH SMT`, `BEARISH SMT (inverse)`, `BULLISH SMT`, `BULLISH SMT (inverse)`.
- Returns a deduplicated, time-sorted `pd.DataFrame` with columns: `time`, `type`, `price_a`, `price_b`, `description`.

### 4. `main()` — lines 209–254
Hardcoded configuration constants (`PERIOD`, `INTERVAL`, `LOOKBACK`, `TOLERANCE`), orchestrates data fetch → detection → console output → CSV export.

## Known Syntax Issues

The file as uploaded contains formatting artifacts that make it **non-executable as-is**:

1. **Triple backtick fences inside function bodies** — lines 39, 60, 201, 215 contain bare ` ``` ` markers that are not valid Python and will cause `SyntaxError`. These appear to be Markdown code-fence remnants that were accidentally included.
2. **Malformed main guard** — line 253 reads `if **name** == **main**:` instead of `if __name__ == "__main__":`. This is likely a Markdown bold-rendering artifact.
3. **Missing indentation** — `main()` body (lines 210–213) is not indented under the `def` statement.

Before running or extending the code, these issues must be fixed.

## Configuration Constants (inside `main()`)

| Constant    | Default | Meaning                                              |
|-------------|---------|------------------------------------------------------|
| `PERIOD`    | `'60d'` | Lookback window of data to download from Yahoo       |
| `INTERVAL`  | `'1h'`  | Candle timeframe                                     |
| `LOOKBACK`  | `5`     | Candles on each side required to confirm a swing     |
| `TOLERANCE` | `3`     | Max candle offset to match a swing across both pairs |

## Output

**Console** — one block per signal:
```
🔴  [2026-04-10 14:00]  BEARISH SMT
  EUR/USD: 1.09231  |  GBP/USD: 1.27845
  EUR/USD made a HIGHER high ... Bearish reversal probable.
```

**CSV** — `smt_signals.csv` written to the current working directory with columns: `time`, `type`, `price_a`, `price_b`, `description`.

## Development Conventions

- **Single-file layout** — keep all logic in `smt.py` unless the file grows significantly.
- **No external config** — parameters live as constants at the top of `main()`.
- **Type hints** — all public functions use Python type hints; maintain this.
- **pandas-centric** — data flows as DataFrames throughout; avoid converting to raw lists/dicts mid-pipeline.
- **No global state** — functions are pure (except I/O in `fetch_data` and `main`).

## Suggested Improvements (not yet implemented)

- Add `requirements.txt` for reproducible installs.
- Fix the three syntax issues described above.
- Add `--period`, `--interval`, `--lookback`, `--tolerance` CLI arguments via `argparse`.
- Add a `.gitignore` to exclude `smt_signals.csv` and `__pycache__/`.
- Add basic unit tests for `find_swings` and `detect_smt_divergence` using synthetic DataFrames.
