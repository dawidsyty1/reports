import logging
import os
import uuid
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException


def prepare_params(source_file_path: str, signed_url: str) -> dict:
    click_able_a = f'<a href="{signed_url}" target="_blank"> link </a>'
    html_content = f"<html> Here is your daily report: {click_able_a} </html>"
    sender_name = os.environ["SENDER_NAME"]
    receiver_name = os.environ["RECEIVER_NAME"]
    sender = {"name": sender_name, "email": receiver_name}
    headers = {"Option Report": str(uuid.uuid4())}

    params = {
        "to": [sender],
        "bcc": [sender],
        "cc": [sender],
        "reply_to": sender,
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
