from dotenv import load_dotenv
from psycopg2.extras import NamedTupleCursor
from twilio.rest import Client
from utils import DatabaseLogHandler, DB_CONN_PARAMS, document_sms
from datetime import datetime, timezone
from collections import namedtuple
import logging
import os
import psycopg2
import time

logger = logging.getLogger('database_logger')
logger.setLevel(logging.INFO)
log_handler = DatabaseLogHandler(DB_CONN_PARAMS)
logger.addHandler(log_handler)

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
            (instrument_id, )
        )
        items = cursor.fetchall()
    return items

def add_item_to_responses(
        connection, # psycopg2 doesn't support type hinting
        phone_number: str, 
        item_text: str, 
        item_id: int,
        opens_datetime: datetime = None
        ) -> None:
    """
    The responses table will be pre-filled with items, and responses will be
    stored here by the API when invoked through Twilio
    """
    if not opens_datetime:
        opens_datetime = datetime.now(timezone.utc) 
    
    connection.cursor().execute(
        """
        INSERT INTO responses (phone_number, item_text, item_id, opens_datetime, status)
        VALUES (%s, %s, %s, %s, %s);
        """, 
        (phone_number, item_text, item_id, opens_datetime, "open")
    )

# Twilio-related
load_dotenv(".env")
messaging_service_sid = os.environ["MESSAGING_SERVICE_SID"]
client = Client(
    os.environ["TWILIO_ACCOUNT_SID"], 
    os.environ["TWILIO_AUTH_TOKEN"]
)
logger.info("Initialised Client")

def main():
    with psycopg2.connect(**DB_CONN_PARAMS) as conn:
        logger.info("Connected to db and ready to process user request")
        iterations = fetch_iterations(conn)
        
        for iter in iterations:
            items = fetch_items(
                connection=conn, 
                instrument_id=iter.instrument_id
            )
            
            for item in items:
                add_item_to_responses(
                    connection=conn, 
                    phone_number=iter.phone_number, 
                    item_text=item.item_text,
                    item_id=item.item_id
                )
            
            add_item_to_responses(
                connection=conn,
                phone_number=iter.phone_number,
                item_text="Tak for din hjælp!",
                item_id=None
            )

            conn.cursor().execute(
                "UPDATE iterations SET is_open = true WHERE iteration_id = %s;",
                (iter.iteration_id, )
            )

            message = client.messages.create(
                to=iter.phone_number,
                body=iter.message_body,
                messaging_service_sid=messaging_service_sid
            )

            document_sms(
                connection=conn,
                phone_number=iter.phone_number,
                message_body=iter.message_body,
                direction="outbound"
            )

            conn.commit()

            logger.info(
                f"{iter.phone_number} invited to new round. Message SID: {message.sid}"
            )
        else:
            logger.info("No pending iterations")

if __name__ == "__main__":
    logger.info("Starting the starter app")

    while True:
        try:
            main()
        except Exception as e:
            error_msg = getattr(e, "message", repr(e))
            logger.fatal(f"main() fails. Error message: {error_msg}")

        SECONDS_PER_HOUR = 60 * 60
        time.sleep(SECONDS_PER_HOUR / 2)
