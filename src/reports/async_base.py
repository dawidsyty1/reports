from dataclasses import dataclass
import logging
from typing import List
from concurrent.futures import ProcessPoolExecutor, as_completed
from openbb_terminal.reports import widget_helpers as widgets
from reports.base import Report

@dataclass
class AsyncReport(Report):
    multiprocessing: bool = False

    def process_futures(self, futures):
        for future in as_completed(futures):
            try
                htmlcode, symbol = future.result()
                self.body += widgets.add_tab(symbol, htmlcode)
            except TypeError as errors:
                logging.warning(f"Failed to process {symbol}: {errors}")

    def process_async(self):
        with ProcessPoolExecutor(max_workers=len(self.tickers)) as executor:
            futures = [
                executor.submit(self.retry_processing, symbol)
                for symbol in self.tickers
            ]
            self.process_futures(futures)


    def process(self):
        if self.multiprocessing:
            logging.info(f"Processing report in multiprocessing mode...")
            self.process_async()
        else:
            logging.info(f"Processing report in normal mode...")
            super().process()
