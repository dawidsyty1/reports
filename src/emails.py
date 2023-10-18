import logging
import os

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException


def prepare_params(source_file_path: str, signed_url: str) -> dict:
    click_able_a = f'<a href="{signed_url}" target="_blank"> link </a>'
    html_content = f"<html> Here is your daily report: {click_able_a} </html>"

    sender = {"name": "Dawid Syty", "email": "dawid.syty1@gmail.com"}
    to = [{"email": "dawid.syty1@gmail.com", "name": "Dawid Syty"}]
    cc = [{"email": "dawid.syty1@gmail.com", "name": "Dawid Syty"}]
    bcc = [{"name": "Dawid Syty", "email": "dawid.syty1@gmail.com"}]
    reply_to = {"email": "dawid.syty1@gmail.com", "name": "Dawid Syty"}
    headers = {"Some-Custom-Name": "unique-id-1234"}

    params = {
        "to": to,
        "bcc": bcc,
        "cc": cc,
        "reply_to": reply_to,
        "headers": headers,
        "html_content": html_content,
        "sender": sender,
        "subject": source_file_path,
    }
    return params


def send_email(source_file_path: str, signed_url: str):
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key["api-key"] = os.environ["SMTP_API_KEY"]

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )
    params = prepare_params(source_file_path, signed_url)
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(**params)

    try:
        api_response = api_instance.send_transac_email(send_smtp_email)
        logging.info(api_response)
    except ApiException as e:
        logging.error(f"Exception when calling SMTPApi->send_transac_email: {e}\n")
