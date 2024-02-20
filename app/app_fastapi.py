# TODO: use aiopg for async postgres queries
# TODO: make validator to ensure only Twilio can call the endpoint

from collections import namedtuple
from datetime import datetime, timezone
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import PlainTextResponse
from psycopg2.extras import NamedTupleCursor
from utils import DatabaseLogHandler, DB_CONN_PARAMS, document_sms, MessagingResponse
import hashlib
import uvicorn
import inspect
import json
import logging
import psycopg2
import time

logger = logging.getLogger('database_logger')
logger.setLevel(logging.INFO)
log_handler = DatabaseLogHandler(DB_CONN_PARAMS)
logger.addHandler(log_handler)

# Helper functions
def parse_response(x: str, lower: int = 1, upper: int = 5) -> int | None:
    try: 
        x = int(x)
        return x if lower <= x <= upper else None
    except ValueError:
        return None

def fetch_next_item(connection, phone_number: str) -> namedtuple:
    # psycopg2 doesn't support type hinting
    with connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
        cursor.execute(
            """
            SELECT item_text, response_id
            FROM responses
            WHERE status = 'open'
                AND phone_number = %s
            ORDER BY response_id ASC
            LIMIT 1;
            """,
            (phone_number, )
        )
        item = cursor.fetchone()
    return item

# Update dict of awaiting responses, fetched from database when app launches
with psycopg2.connect(**DB_CONN_PARAMS) as conn:
    with conn.cursor(cursor_factory=NamedTupleCursor) as cursor:
        cursor.execute(
            """
            SELECT phone_number, response_id
            FROM responses
            WHERE status = 'awaiting';
            """
        )
        rows = cursor.fetchall()

awaiting_responses = {row.phone_number: row.response_id for row in rows}

# Set up custom response type
class XmlResponse(Response):
    media_type = "application/xml"

app = FastAPI()

@app.get("/health", response_class=PlainTextResponse)
def health() -> PlainTextResponse:
    return "Service is healthy"

@app.post("/twilio", response_class=XmlResponse)
async def twilio_response(request: Request) -> XmlResponse:
    data = await request.form()
    phone_number = data.get("from", None)
    inbound_body = data.get("message", None)

    resp = MessagingResponse()

    if not phone_number:
        resp.message("Houston, we have a problem")
        logger.critical(
            "Didn't receive a recipient phone number. Twilio request: \n" +
            json.dumps(data)
        )
        return resp.to_xml()
    
    with psycopg2.connect(**DB_CONN_PARAMS) as conn:
        # TODO: don't save response to "thank you message" -- find a way to make this happen

        document_sms(
            connection=conn,
            phone_number=phone_number,
            message_body=inbound_body,
            direction="inbound"
        )

        # TODO: remove later, this is to allow to start over interactively
        if inbound_body == "Restart":
            awaiting_responses.pop(phone_number, None)

            conn.cursor().execute(
                "UPDATE iterations SET is_open = true WHERE phone_number = %s;",
                (phone_number, )
            )

            conn.cursor().execute(
                """
                UPDATE responses SET status = 'open', response = NULL
                WHERE phone_number = %s
                """,
                (phone_number, )
            )

            with conn.cursor(cursor_factory=NamedTupleCursor) as cursor:
                cursor.execute(
                    """
                    SELECT message_body 
                    FROM iterations 
                    WHERE phone_number = %s
                        AND is_open = true
                    ORDER BY iteration_id DESC
                    LIMIT 1;
                    """,
                    (phone_number, )
                )
                outbound_body = cursor.fetchone().message_body

            resp.message(outbound_body)
            document_sms(
                connection=conn,
                phone_number=phone_number,
                message_body=outbound_body,
                direction="outbound"
            )
            return resp.to_xml()
        
        with conn.cursor(cursor_factory=NamedTupleCursor) as cursor:
            cursor.execute(
                """
                SELECT COUNT(response_id) AS n
                FROM responses
                WHERE phone_number = %s
                    AND status = 'awaiting';
                """,
                (phone_number, )
            )
            n_responses_waiting_for_user = cursor.fetchone().n

        parsed_response = parse_response(inbound_body)

        if n_responses_waiting_for_user == 0:
            awaiting_responses.pop(phone_number, None)
        elif parsed_response:
            conn.cursor().execute(
                """
                UPDATE responses SET response = %s, status = 'closed'
                WHERE response_id = %s 
                    AND phone_number = %s
                    AND status = 'awaiting'
                """,
                (parsed_response, awaiting_responses[phone_number], phone_number)
            )
        else:
            outbound_body = "Husk svare med blot èt heltal fra listen ovenfor."
            resp.message(outbound_body)
            document_sms(
                connection=conn,
                phone_number=phone_number,
                message_body=outbound_body,
                direction="outbound"
            )
            return resp.to_xml()

        item = fetch_next_item(conn, phone_number)

        if item:
            awaiting_responses[phone_number] = item.response_id
            outbound_body = item.item_text
            
            conn.cursor().execute(
                """
                UPDATE responses
                SET status = 'awaiting', status_datetime = %s
                WHERE response_id = %s;
                """,
                (datetime.now(timezone.utc), item.response_id)
            )
        else:
            # TODO: consider to mention we'll be in touch again
            error_code = hashlib.sha256(f"{time.time()}".encode("utf-8"))
            error_code = error_code.hexdigest()[:7]
            outbound_body = inspect.cleandoc(
                f"""\
                Der ser ikke ud til at være nogle åbne spørgsmål til dig. 
                Svar 'Restart' for at starte forfra.\
                """
                # Er dette en fejl, bedes du kontakte os med følgende fejlkode: {error_code}.
            )
        
        resp.message(outbound_body)

        document_sms(
            connection=conn,
            phone_number=phone_number,
            message_body=outbound_body,
            direction="outbound"
        )
    
    return resp.to_xml()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
