import hashlib
import inspect
import json
import time

import uvicorn
from fastapi import (
    Depends,
    FastAPI,
    Request,
)
from fastapi.responses import JSONResponse
from sqlalchemy import (
    and_,
    func,
    select,
    update,
)
from sqlalchemy.engine import Engine
from utils.api import (
    XmlResponse,
    dump_request,
    fetch_awaiting_responses,
    fetch_next_item,
    parse_response,
    to_xml_response,
)
from utils.db import (
    make_engine,
    make_session,
)
from utils.logging import LOGGER
from utils.orm import (
    Iteration,
    Message,
    Response,
)

with open("/run/secrets/cpsms_webhook_token", "r") as f:
    CPSMS_WEBHOOK_TOKEN: str = f.readline()

# TODO: should probably use environment variable,
# perhaps even defining once without Depends()
awaiting_responses = fetch_awaiting_responses(make_engine())

app = FastAPI()


@app.middleware("http")
def validate_token_middleware(request: Request, call_next):
    token = request.query_params.get("token")

    if token != CPSMS_WEBHOOK_TOKEN and request.url.path != "/health":
        return JSONResponse(
            status_code=403, content={"details": "Invalid token"}
        )

    response = call_next(request)
    return response


@app.get("/health", response_class=JSONResponse)
def health() -> JSONResponse:
    return {"status": "Service is healthy"}


@app.get("/aquaicu", response_class=XmlResponse)
def sms_response(
    request: Request, engine: Engine = Depends(make_engine)
) -> XmlResponse:

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

    with make_session(engine) as session:
        new_message = Message(
            phone_number=phone_number,
            message_body=inbound_body,
            direction="inbound",
        )
        session.add(new_message)

    # TODO: remove later, this is to allow to start over interactively
    if inbound_body == "Restart":
        awaiting_responses.pop(phone_number, None)

        # TODO: remove later, this is to allow to start over interactively
        if inbound_body == "Restart":
            awaiting_responses.pop(phone_number, None)

            with make_session(engine) as session:
                stmt = (
                    update(Iteration)
                    .where(Iteration.phone_number == phone_number)
                    .values(is_open=False, updated_by="fastapi")
                )
                session.execute(stmt)

                stmt = (
                    update(Response)
                    .where(
                        Response.phone_number == phone_number,
                    )
                    .values(status="open", response=None, updated_by="fastapi")
                )
                session.execute(stmt)

        with make_session(engine) as session:
            stmt = (
                select(Iteration)
                .where(
                    and_(
                        Iteration.phone_number == phone_number,
                        Iteration.is_open,
                    )
                )
                .order_by(Iteration.iteration_id.desc())
            )
            outbound_body = session.scalars(stmt).first()

            new_message = Message(
                phone_number=phone_number,
                message_body=outbound_body,
                direction="outbound",
            )
            session.add(new_message)

        return to_xml_response(outbound_body)

    with make_session(engine) as session:
        stmt = select(func.count(Response.response_id)).where(
            and_(
                Response.phone_number == phone_number,
                Response.status == "awaiting",
            )
        )
        n_responses_waiting_for_user = session.scalar(stmt)

    parsed_response = parse_response(inbound_body)

    if n_responses_waiting_for_user == 0:
        awaiting_responses.pop(phone_number, None)
    elif parsed_response:
        stmt = (
            update(Response)
            .where(
                and_(
                    Response.response_id == awaiting_responses[phone_number],
                    Response.phone_number == phone_number,
                    Response.status == "awaiting",
                )
            )
            .values(
                response=parsed_response, status="closed", updated_by="fastapi"
            )
        )
        with make_session(engine) as session:
            session.execute(stmt)

    else:
        outbound_body = "Husk svare med blot èt heltal fra listen ovenfor."

        with make_session(engine) as session:
            new_message = Message(
                phone_number=phone_number,
                message_body=outbound_body,
                direction="outbound",
            )
            session.add(new_message)

        return to_xml_response(outbound_body)

    item = fetch_next_item(engine, phone_number)

    if item:
        awaiting_responses[phone_number] = item.response_id
        outbound_body = item.item_text

        stmt = (
            update(Response)
            .where(Response.response_id == item.response_id)
            .values(status="awaiting", updated_by="fastapi")
        )
        with make_session(engine) as session:
            session.execute(stmt)

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

    with make_session(engine) as session:
        new_message = Message(
            phone_number=phone_number,
            message_body=outbound_body,
            direction="outbound",
        )
        session.add(new_message)

    return to_xml_response(outbound_body)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
