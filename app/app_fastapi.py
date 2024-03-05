# TODO: use aiopg for async postgres queries

import hashlib
import inspect
import json
import time

import psycopg2
import uvicorn
from fastapi import (
    FastAPI,
    Request,
)
from fastapi.responses import JSONResponse
from psycopg2.extras import NamedTupleCursor
from utils.api import (
    XmlResponse,
    dump_request,
    fetch_awaiting_responses,
    fetch_next_item,
    parse_response,
    to_xml_response,
)
from utils.db import (
    DB_CONN_PARAMS,
    PROD_SCHEMA,
)
from utils.logging import LOGGER
from utils.sms import document_sms

with psycopg2.connect(**DB_CONN_PARAMS) as conn:
    awaiting_responses = fetch_awaiting_responses(conn)

app = FastAPI()


@app.get("/health", response_class=JSONResponse)
def health() -> JSONResponse:
    return {"status": "Service is healthy"}


@app.get("/aquaicu", response_class=XmlResponse)
async def sms_response(request: Request) -> XmlResponse:
    data = request.query_params
    phone_number = data.get("from", None)
    inbound_body = data.get("message", None)

    dump_request(request, "request")

    if not phone_number:
        LOGGER.critical(
            "Didn't receive a recipient phone number. Request: \n"
            + json.dumps(data)
        )
        return to_xml_response("Houston, we have a problem")

    with psycopg2.connect(**DB_CONN_PARAMS) as conn:
        # TODO: don't save response to "thank you message"

        document_sms(
            connection=conn,
            phone_number=phone_number,
            message_body=inbound_body,
            direction="inbound",
        )

        # TODO: remove later, this is to allow to start over interactively
        if inbound_body == "Restart":
            awaiting_responses.pop(phone_number, None)

            conn.cursor().execute(
                """
                UPDATE {}.iterations
                SET is_open = true, updated_by = 'fastapi'
                WHERE phone_number = %s
                """.format(
                    PROD_SCHEMA
                ),
                (phone_number,),
            )

            conn.cursor().execute(
                """
                UPDATE {}.responses
                SET status = 'open', response = NULL, updated_by = 'fastapi'
                WHERE phone_number = %s
                """.format(
                    PROD_SCHEMA
                ),
                (phone_number,),
            )

            with conn.cursor(cursor_factory=NamedTupleCursor) as cursor:
                cursor.execute(
                    """
                    SELECT message_body
                    FROM {}.iterations
                    WHERE phone_number = %s
                        AND is_open = true
                    ORDER BY iteration_id DESC
                    LIMIT 1;
                    """.format(
                        PROD_SCHEMA
                    ),
                    (phone_number,),
                )
                outbound_body = cursor.fetchone().message_body

            document_sms(
                connection=conn,
                phone_number=phone_number,
                message_body=outbound_body,
                direction="outbound",
            )
            return to_xml_response(outbound_body)

        with conn.cursor(cursor_factory=NamedTupleCursor) as cursor:
            cursor.execute(
                """
                SELECT COUNT(response_id) AS n
                FROM {}.responses
                WHERE phone_number = %s
                    AND status = 'awaiting';
                """.format(
                    PROD_SCHEMA
                ),
                (phone_number,),
            )
            n_responses_waiting_for_user = cursor.fetchone().n

        parsed_response = parse_response(inbound_body)

        if n_responses_waiting_for_user == 0:
            awaiting_responses.pop(phone_number, None)
        elif parsed_response:
            conn.cursor().execute(
                """
                UPDATE {}.responses
                SET response = %s, status = 'closed', updated_by = 'fastapi'
                WHERE response_id = %s
                    AND phone_number = %s
                    AND status = 'awaiting'
                """.format(
                    PROD_SCHEMA
                ),
                (
                    parsed_response,
                    awaiting_responses[phone_number],
                    phone_number,
                ),
            )
        else:
            outbound_body = "Husk svare med blot èt heltal fra listen ovenfor."

            document_sms(
                connection=conn,
                phone_number=phone_number,
                message_body=outbound_body,
                direction="outbound",
            )

            return to_xml_response(outbound_body)

        item = fetch_next_item(conn, phone_number)

        if item:
            awaiting_responses[phone_number] = item.response_id
            outbound_body = item.item_text

            conn.cursor().execute(
                """
                UPDATE {}.responses
                SET status = 'awaiting', updated_by = 'fastapi'
                WHERE response_id = %s;
                """.format(
                    PROD_SCHEMA
                ),
                (item.response_id,),
            )
        else:
            # TODO: consider to mention we'll be in touch again
            error_code = hashlib.sha256(f"{time.time()}".encode("utf-8"))
            error_code = error_code.hexdigest()[:7]
            outbound_body = inspect.cleandoc(
                """\
                Der ser ikke ud til at være nogle åbne spørgsmål til dig.
                Svar 'Restart' for at starte forfra.\
                """
            )

        document_sms(
            connection=conn,
            phone_number=phone_number,
            message_body=outbound_body,
            direction="outbound",
        )

    return to_xml_response(outbound_body)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
