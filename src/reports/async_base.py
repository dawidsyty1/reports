import logging
from typing import List
from concurrent.futures import ProcessPoolExecutor, as_completed
from openbb_terminal.reports import widget_helpers as widgets
from reports.base import Report


class AsyncReport(Report):
    def __init__(
        self,
        author: str,
        report_title: str,
        tickers: List[str],
        multiprocessing: bool = False,
    ) -> None:
        super().__init__(author, report_title, tickers)
        self.multiprocessing = multiprocessing

    def process_async(self):
        with ProcessPoolExecutor(max_workers=len(self.tickers)) as executor:
            futures = []
            for symbol in self.tickers:
                futures.append(executor.submit(self.retry_processing, symbol))

            for future in as_completed(futures):
                htmlcode, symbol = future.result()
                self.body += widgets.add_tab(symbol, htmlcode)

    def process(self):
        if self.multiprocessing:
            logging.info(f"Processing report in multiprocessing mode...")
            self.process_async()
        else:
            logging.info(f"Processing report in normal mode...")
            super().process()
