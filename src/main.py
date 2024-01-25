import logging
import os

import click
import pandas as pd
from emails import send_email
from reports.options import OptionReport, OptionReportV2
from reports.gex import GEXFullReport
from storage import upload_to_storage

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(filename)s %(funcName)s %(message)s",
    level=os.environ.get("LOGLEVEL", "INFO"),
    datefmt="%Y-%m-%d %H:%M:%S",
)

@click.command()
@click.option("--send", default=False, help="Send in to the bucket and send email")
@click.option("--report_type", default="Normal", help="Type of the report")
def process(send, report_type):

    if report_type == "GEX":
        report = GEXFullReport(
            author="Dawid S.", report_title="Options Report", tickers=["SPY"], multiprocessing=False
        )
    elif report_type == "US30":
        tickers = pd.read_csv("us30.csv", header=None)[0].tolist()
        tickers = tickers[1:-1]
        report = OptionReportV2(
            author="Dawid S.", report_title="Options Report", tickers=tickers, multiprocessing=True
        )
    else:
        tickers = ["^SPX", "^VIX", "^DJI", "^TYX", "SPY", "SPXL", "QQQ", "IWM", "DIA", "GLD", "TLT", "SMH", "SOXL", "USO"]

        report = OptionReportV2(
            author="Dawid S.", report_title="Options Report", tickers=tickers, multiprocessing=True
        )

    report.process()
    full_file_name = report.save_to_html()
    if send:
        signed_url = upload_to_storage(full_file_name)
        send_email(full_file_name, signed_url)


if __name__ == "__main__":
    process()
