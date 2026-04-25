"""
Retrieve NASDAQ 100 quotes using yfinance.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime


NASDAQ100_TICKERS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "GOOG", "TSLA", "AVGO", "COST",
    "NFLX", "ASML", "AMD", "CSCO", "ADBE", "PEP", "QCOM", "INTU", "TXN", "AMAT",
    "AMGN", "ISRG", "HON", "BKNG", "SBUX", "VRTX", "LRCX", "REGN", "ADP", "GILD",
    "MU", "ADI", "PANW", "MELI", "KLAC", "SNPS", "CDNS", "INTC", "CTAS", "MDLZ",
    "CSX", "PYPL", "ORLY", "MRVL", "NXPI", "MNST", "MAR", "WDAY", "ABNB", "PAYX",
    "PCAR", "KDP", "ADSK", "ROST", "FTNT", "ODFL", "FAST", "CPRT", "DXCM", "IDXX",
    "VRSK", "EA", "BIIB", "EXC", "CTSH", "DLTR", "XEL", "GEHC", "KHC", "FANG",
    "ON", "BKR", "CCEP", "TTWO", "ZS", "CDW", "ANSS", "WBD", "TEAM", "DDOG",
    "GFS", "SIRI", "CRWD", "ILMN", "MDB", "CEG", "WBA", "ALGN", "MRNA", "ENPH",
    "LCID", "RIVN", "SMCI", "ARM", "MSTR", "PLTR", "APP", "COIN", "HOOD", "TTD",
]


def get_nasdaq100_quotes(tickers: list[str] | None = None) -> pd.DataFrame:
    """
    Fetch the latest quotes for NASDAQ 100 tickers.

    Returns a DataFrame with columns: Ticker, Name, Price, Change, Change%, Volume.
    """
    if tickers is None:
        tickers = NASDAQ100_TICKERS

    print(f"Fetching quotes for {len(tickers)} NASDAQ 100 components...")

    data = yf.download(
        tickers=tickers,
        period="2d",
        interval="1d",
        group_by="ticker",
        auto_adjust=True,
        progress=False,
        threads=True,
    )

    rows = []
    for ticker in tickers:
        try:
            ticker_data = data[ticker] if len(tickers) > 1 else data
            ticker_data = ticker_data.dropna(subset=["Close"])
            if len(ticker_data) < 1:
                continue

            current_close = float(ticker_data["Close"].iloc[-1])
            prev_close = float(ticker_data["Close"].iloc[-2]) if len(ticker_data) >= 2 else None
            volume = float(ticker_data["Volume"].iloc[-1]) if "Volume" in ticker_data.columns else None

            change = current_close - prev_close if prev_close else None
            change_pct = (change / prev_close * 100) if prev_close else None

            rows.append({
                "Ticker": ticker,
                "Price": round(current_close, 2),
                "Change": round(change, 2) if change is not None else None,
                "Change%": round(change_pct, 2) if change_pct is not None else None,
                "Volume": int(volume) if volume is not None else None,
            })
        except (KeyError, IndexError):
            continue

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("Ticker").reset_index(drop=True)
    return df


def print_quotes(df: pd.DataFrame) -> None:
    """Print quotes table to the console."""
    if df.empty:
        print("No data retrieved.")
        return

    print(f"\nNASDAQ 100 Quotes  —  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 65)
    print(f"{'Ticker':<8} {'Price':>10} {'Change':>10} {'Change%':>10} {'Volume':>14}")
    print("-" * 65)

    for _, row in df.iterrows():
        change_str = f"{row['Change']:+.2f}" if row["Change"] is not None else "N/A"
        pct_str = f"{row['Change%']:+.2f}%" if row["Change%"] is not None else "N/A"
        vol_str = f"{row['Volume']:,}" if row["Volume"] is not None else "N/A"
        print(f"{row['Ticker']:<8} {row['Price']:>10.2f} {change_str:>10} {pct_str:>10} {vol_str:>14}")

    print("-" * 65)
    print(f"Total symbols: {len(df)}")


if __name__ == "__main__":
    quotes = get_nasdaq100_quotes()
    print_quotes(quotes)
