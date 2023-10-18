import logging
from pathlib import Path
from typing import List

import pandas as pd
import pytz
from openbb_terminal.helper_funcs import get_user_timezone
from openbb_terminal.reports import widget_helpers as widgets


class Report:
    def __init__(self, author: str, report_title: str, tickers: List[str]) -> None:
        user_time_zone = pytz.timezone(get_user_timezone())
        self.report_date = pd.Timestamp.now(tz=user_time_zone).strftime("%Y-%m-%d")
        self.report_time = pd.Timestamp.now(tz=user_time_zone).strftime("%H:%M")

        self.body = widgets.header(
            author,
            self.report_date,
            self.report_time,
            "",
            report_title,
            plotly_js=False,
        )
        self.body += '<a id="top"></a>'
        self.body += widgets.tablinks(tickers)
        self.tickers = tickers

    def process_symbol(self, symbol: str):
        htmlcode = widgets.h(1, f"Simple analysis for {symbol}:")
        self.body += widgets.add_tab(symbol, htmlcode)

    def process(self):
        for symbol in self.tickers:
            self.process_symbol(symbol)

    def report_file_full_path(self, raports_dir: str = "reports") -> str:
        file_path = Path(raports_dir, self.report_date)
        file_path.mkdir(parents=True, exist_ok=True)
        file_path = Path(file_path, self.report_time)
        file_path = str(file_path) + ".html"
        return file_path

    def save_to_html(self, raports_dir: str = "reports"):
        self.body += '<a class="button" href="#top">Back to top</a>'
        self.body += widgets.tab_clickable_and_save_evt()
        stylesheet = widgets.html_report_stylesheet()
        report = widgets.html_report(
            title="Option Report", stylesheet=stylesheet, body=self.body
        )
        full_file_name = self.report_file_full_path(raports_dir)

        with open(full_file_name, "w", encoding="utf-8") as fh:
            fh.write(report)
            logging.info(f"Saved: {full_file_name} \n\r")
        return full_file_name