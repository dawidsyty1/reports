import pandas as pd
import logging
import yfinance as yf
from datetime import datetime
from storage import upload_to_storage
from pathlib import Path


sorted_chain_columns = [
    "optionType",
    "expiration",
    "strike",
    "lastPrice",
    "bid",
    "ask",
    "openInterest",
    "volume",
]


def get_full_option_chain(symbol: str, quiet: bool = False) -> pd.DataFrame:
    ticker = yf.Ticker(symbol)
    dates = ticker.options

    options = pd.DataFrame()

    for _date in dates:
        calls = ticker.option_chain(_date).calls
        calls["optionType"] = "call"
        calls["expiration"] = _date
        calls = calls[sorted_chain_columns]
        puts = ticker.option_chain(_date).puts
        puts["optionType"] = "put"
        puts["expiration"] = _date
        puts = puts[sorted_chain_columns]

        temp = pd.merge(calls, puts, how="outer", on="strike")
        temp["expiration"] = _date
        options = (
            pd.concat([options, pd.concat([calls, puts])], axis=0)
            .fillna(0)
            .reset_index(drop=True)
        )
    return options


def pull_and_push_to_bucket(symbol: str):
    report_date: str = datetime.now().strftime("%Y-%m-%d")
    report_time: str = datetime.now().strftime("%H:%M")
    chain = get_full_option_chain(symbol)

    path = Path(f"chains/{symbol}/{report_date}/{report_time}/")
    path.mkdir(parents=True, exist_ok=True)
    file_path = f"{str(path)}/{symbol}.csv"
    chain.to_csv(file_path)

    upload_to_storage(file_path)


if __name__ == "__main__":
    tickers = ["^SPX", "^VIX", "SPY", "SPXL", "QQQ", "IWM", "DIA", "GLD", "TLT", "SMH", "SOXL", "USO"]
    for ticker in tickers:
        try:
            logging.info(f"fetching {ticker}")
            pull_and_push_to_bucket(ticker)
        except Exception as e:
            logging.error(f"error while processing {ticker}: {e}")
