import json
import logging
import os
from datetime import (
    datetime,
    timezone,
)

import requests
from fastapi import Response
from utils.db import PROD_SCHEMA


def document_sms(
    connection, phone_number: str, message_body: str, direction: str
) -> None:
    timestamp = datetime.now(timezone.utc)
    connection.cursor().execute(
        """
        INSERT INTO {}.messages
            (sent_datetime, phone_number, message_body, direction)
        VALUES (%s, %s, %s, %s);
        """.format(
            PROD_SCHEMA
        ),
        (timestamp, phone_number, message_body, direction),
    )


def send_sms(
    to: int = None, message: str = None, logger: logging.Logger = None
) -> Response:
    payload = {"to": to, "message": message}
    headers = {"Authorization": "Basic " + os.environ["CPSMS_API_TOKEN"]}

    if logger:
        logger.info(f"Trying to send payload {json.dumps(payload)} to {to}")

    message = requests.post(
        url="https://api.cpsms.dk/v2/send", json=payload, headers=headers
    )

    if logger:
        logger.info(message.text)

    return message
