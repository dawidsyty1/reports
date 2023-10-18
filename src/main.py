import click

from emails import send_email
from options import OptionReport
from storage import upload_to_storage


@click.command()
@click.option("--send", default=False, help="Send in to the bucket and send email")
def process(send):
    report = OptionReport(
        author="Dawid S.", report_title="Options Report", tickers=["SPY"]
    )

    report.process()
    full_file_name = report.save_to_html()
    if send:
        signed_url = upload_to_storage(full_file_name)
        send_email(full_file_name, signed_url)


if __name__ == "__main__":
    process()
