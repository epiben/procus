import datetime
import json
from collections import namedtuple

from dotenv import load_dotenv
from fastapi import (
    Request,
    Response,
)
from psycopg2.extras import NamedTupleCursor
from utils.db import PROD_SCHEMA

load_dotenv(".env")


class XmlResponse(Response):
    media_type = "application/xml;charset=utf-8"


def to_xml_response(response: str = None) -> XmlResponse:
    # See https://www.cpsms.dk/files/CPSMS_2vejs_API.pdf

    if not response or response == "":
        body = "<cancel></cancel>"
    else:
        body = f"<message>{response}</message>"

    out = [
        "<?xml version='1.0' encoding='utf-8'?>",
        "<reply>",
        body,
        "</reply>",
    ]

    return "\n".join(out)


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
            FROM {}.responses
            WHERE status = 'open'
                AND phone_number = %s
            ORDER BY response_id ASC
            LIMIT 1;
            """.format(
                PROD_SCHEMA
            ),
            (phone_number,),
        )
        item = cursor.fetchone()
    return item


# Build dict of awaiting responses when app launches
# the dict is updated when the /aquaicu endpoint is invoked (when appropriate)
def fetch_awaiting_responses(connection) -> dict:
    with connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
        cursor.execute(
            """
            SELECT phone_number, response_id
            FROM {}.responses
            WHERE status = 'awaiting';
            """.format(
                PROD_SCHEMA
            )
        )
        rows = cursor.fetchall()

    return {row.phone_number: row.response_id for row in rows}


async def dump_request(request: Request, file_path: str = None) -> None:
    request_as_dict = {
        "method": request.method,
        "url_path": request.url.path,
        "query_params": dict(request.query_params),
        "headers": dict(request.headers),
        "client": request.client,
        "body_content": (await request.body()).decode(),
    }

    unix_epochs = int(datetime.datetime.now().timestamp())
    with open(f"/persistent_storage/{file_path}_{unix_epochs}.json", "w") as f:
        json.dump(request_as_dict, f)
