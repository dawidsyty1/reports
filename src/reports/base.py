import logging
from pathlib import Path
from typing import List, Tuple
import pandas as pd
import pytz
from openbb_terminal.helper_funcs import get_user_timezone
from openbb_terminal.reports import widget_helpers as widgets

from dataclasses import dataclass

@dataclass
class Report:
    tickers : List[str]
    author: str
    report_title: str
    report_date : str = pd.Timestamp.now(tz=pytz.timezone(get_user_timezone())).strftime("%Y-%m-%d")
    report_time : str = pd.Timestamp.now(tz=pytz.timezone(get_user_timezone())).strftime("%H:%M")
    body : str = None

    def __post_init__(self) -> None:
        self.body = widgets.header(
            self.author,
            self.report_date,
            self.report_time,
            "",
            self.report_title,
            plotly_js=False,
        )
        self.body += '<a id="top"></a>'
        self.body += widgets.tablinks(self.tickers)


    def process_symbol(self, symbol: str) -> Tuple[str, str]:
        htmlcode = widgets.h(1, f"Simple analysis for {symbol}:")
        return htmlcode, symbol

    def retry_processing(self, symbol: str, retry: int=3) -> Tuple[str, str]:
        try:
            return self.process_symbol(symbol)
        except Exception as error:
            if retry:
                return self.retry_processing(symbol, retry - 1)
            raise error
    
    def process(self):
        for symbol in self.tickers:
            htmlcode, symbol = self.retry_processing(symbol)
            self.body += widgets.add_tab(symbol, htmlcode)

    def report_file_full_path(self, raports_dir: str = "reports") -> str:
        file_path = Path(raports_dir, self.report_date)
        file_path.mkdir(parents=True, exist_ok=True)
        file_path = Path(file_path, self.report_time)
        file_path = str(file_path) + ".html"
        return file_path

    def save_to_html(self, raports_dir: str = "reports") -> str:
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
