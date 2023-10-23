import logging
from pathlib import Path
from typing import List
from concurrent.futures import ProcessPoolExecutor, as_completed
import pandas as pd
import pytz
from openbb_terminal.helper_funcs import get_user_timezone
from openbb_terminal.reports import widget_helpers as widgets
from reports.base import Report

class AsyncReport(Report):
    def process_async(self):
        with ProcessPoolExecutor(max_workers=len(self.tickers)) as executor:
            futures = []
            for symbol in self.tickers:
                futures.append(executor.submit(self.retry_processing, symbol))

            for future in as_completed(futures):
                htmlcode, symbol = future.result()
                self.body += widgets.add_tab(symbol, htmlcode)

    def process(self):
        self.process_async()
