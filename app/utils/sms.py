import json
import logging
from datetime import (
    datetime,
    timezone,
)

import requests
from fastapi import Response
from sqlalchemy.engine import Engine
from utils.db import make_session
from utils.orm import Message


def document_sms(
    engine: Engine, phone_number: str, message_body: str, direction: str
) -> None:
    with make_session(engine) as session:
        session.add(
            Message(
                sent_datime=datetime.now(timezone.utc),
                phone_number=phone_number,
                message_body=message_body,
                direction=direction,
            )
        )


def send_sms(
    to: int = None,
    message: str = None,
    token: str = None,
    logger: logging.Logger = None,
) -> Response:
    payload = {"to": to, "message": message}
    headers = {"Authorization": f"Basic {token}"}

    if logger:
        logger.info(f"Trying to send payload {json.dumps(payload)} to {to}")

    message = requests.post(
        url="https://api.cpsms.dk/v2/send", json=payload, headers=headers
    )

    if logger:
        logger.info(message.text)

    return message
