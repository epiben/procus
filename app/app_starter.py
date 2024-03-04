import logging
import time
from collections import namedtuple
from datetime import (
    datetime,
    timezone,
)

import psycopg2
import requests
from psycopg2.extras import NamedTupleCursor
from utils.db import DB_CONN_PARAMS
from utils.logging import LOGGER
from utils.sms import (
    document_sms,
    send_sms,
)


# Helper functions
def fetch_iterations(connection) -> list[namedtuple]:
    with connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
        cursor.execute(
            """
            SELECT iteration_id, phone_number, instrument_id, message_body
            FROM iterations
            WHERE is_open IS false
                AND opens_datetime <= now();
            """
        )
        iterations = cursor.fetchall()
    return iterations


def fetch_items(connection, instrument_id: int) -> list[namedtuple]:
    with connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
        cursor.execute(
            """
            SELECT item_id, item_text
            FROM items
            WHERE instrument_id = %s
            """,
            (instrument_id,),
        )
        items = cursor.fetchall()
    return items


def add_item_to_responses(
    connection,  # psycopg2 doesn't support type hinting
    phone_number: str,
    item_text: str,
    item_id: int,
    opens_datetime: datetime = None,
) -> None:
    """
    The responses table will be pre-filled with items, and responses will be
    stored here by the API when invoked through Twilio
    """
    if not opens_datetime:
        opens_datetime = datetime.now(timezone.utc)

    connection.cursor().execute(
        """
        INSERT INTO responses (
            phone_number
            , item_text
            , item_id
            , opens_datetime
            , status
        )
        VALUES (%s, %s, %s, %s, %s);
        """,
        (phone_number, item_text, item_id, opens_datetime, "open"),
    )


def main():
    with psycopg2.connect(**DB_CONN_PARAMS) as conn:
        LOGGER.info("Connected to db and ready to process user request")
        iterations = fetch_iterations(conn)

        for iter in iterations:
            items = fetch_items(
                connection=conn, instrument_id=iter.instrument_id
            )

            for item in items:
                add_item_to_responses(
                    connection=conn,
                    phone_number=iter.phone_number,
                    item_text=item.item_text,
                    item_id=item.item_id,
                )

            add_item_to_responses(
                connection=conn,
                phone_number=iter.phone_number,
                item_text="Tak for din hjælp!",
                item_id=None,
            )

            message = send_sms(
                to=iter.phone_number, message=iter.message_body, logger=LOGGER
            )

            if message.status_code == requests.codes.ok:
                conn.cursor().execute(
                    """
                    UPDATE iterations SET is_open = true
                    WHERE iteration_id = %s
                    """,
                    (iter.iteration_id,),
                )
            else:
                logging.error(
                    f"Failed invite {iter.phone_number} to new around. "
                    + "Iteration_id: {iter.iteration_id}"
                )

            document_sms(
                connection=conn,
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
            main()
        except Exception as e:
            error_msg = getattr(e, "message", repr(e))
            LOGGER.fatal(f"main() fails. Error message: {error_msg}")
            # TODO: send to pushover or similar

        SECONDS_PER_HOUR = 60 * 60
        time.sleep(SECONDS_PER_HOUR / 2)
