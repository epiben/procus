import logging
import time

import requests
from sqlalchemy import update
from sqlalchemy.engine import Engine
from utils.db import (
    make_engine,
    make_session,
)
from utils.logging import LOGGER
from utils.orm import Iteration
from utils.sms import (
    document_sms,
    send_sms,
)
from utils.starter import (
    add_item_to_responses,
    fetch_items,
    fetch_iterations_to_open,
)

with open("/run/secrets/cpsms_api_token", "r") as f:
    CPSMS_API_TOKEN: str = f.readline()


def main(engine: Engine):
    LOGGER.info("Connected to db and ready to process user request")
    iterations = fetch_iterations_to_open(engine)

    for iter in iterations:
        items = fetch_items(engine=engine, instrument_id=iter.instrument_id)

        for item in items:
            add_item_to_responses(
                engine=engine,
                phone_number=iter.phone_number,
                item_text=item.item_text,
                item_id=item.item_id,
            )

        add_item_to_responses(
            engine=engine,
            phone_number=iter.phone_number,
            item_text="Tak for din hjælp!",
            item_id=None,
        )

        message = send_sms(
            to=iter.phone_number,
            message=iter.message_body,
            token=CPSMS_API_TOKEN,
            logger=LOGGER,
        )

        if message.status_code == requests.codes.ok:
            stmt = (
                update(Iteration)
                .where(Iteration.iteration_id == iter.iteration_id)
                .values(is_open=True, updated_by="starter")
            )
            with make_session(engine) as session:
                session.execute(stmt)
        else:
            logging.error(
                f"Could not invite {iter.phone_number} to new around. "
                + "Iteration_id: {iter.iteration_id}"
            )

        document_sms(
            engine=engine,
            phone_number=iter.phone_number,
            message_body=iter.message_body,
            direction="outbound",
        )

        LOGGER.info(f"{iter.phone_number} invited to new round.)")
    else:
        LOGGER.info("No pending iterations")


if __name__ == "__main__":
    LOGGER.info("Starting the starter app")

    while True:
        try:
            engine: Engine = make_engine()
            main(engine)
        except Exception as e:
            error_msg: str = getattr(e, "message", repr(e))
            LOGGER.fatal(f"main() fails. Error message: {error_msg}")
            # TODO: send to pushover or similar

        SECONDS_PER_HOUR = 60 * 60
        time.sleep(SECONDS_PER_HOUR / 2)
