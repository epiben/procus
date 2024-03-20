from collections import namedtuple
from datetime import (
    datetime,
    timezone,
)

from sqlalchemy import (
    and_,
    func,
    not_,
)
from sqlalchemy.engine import Engine
from utils.db import make_session
from utils.orm import (
    Iteration,
    Response,
)


def fetch_iterations_to_open(engine: Engine) -> list[namedtuple]:
    """
    Fetch iterations to open from the database. These are iterations that
    are still closed by are set to open before now()
    """

    with make_session(engine) as session:
        iterations = (
            session.query(Iteration)
            .filter(
                and_(
                    not_(Iteration.is_open),
                    Iteration.opens_datetime <= func.now(),
                )
            )
            .all()
        )
    return iterations


def fetch_items(engine: Engine, instrument_id: int) -> list[namedtuple]:
    """Fetch items for a given instrument_id from the database."""

    with make_session(engine) as session:
        items = (
            session.query(Response.item_id, Response.item_text)
            .filter(Response.instrument_id == instrument_id)
            .all()
        )
    return items


def add_item_to_responses(
    engine: Engine,
    phone_number: str,
    item_text: str,
    item_id: int,
    opens_datetime: datetime = None,
) -> None:
    """
    The responses table will be pre-filled with items, and responses will be
    stored here by the API when invoked through SMS gateway
    """

    if not opens_datetime:
        opens_datetime = datetime.now(timezone.utc)

    with make_session(engine) as session:
        session.add(
            Response(
                phone_number=phone_number,
                item_text=item_text,
                item_id=item_id,
                opens_datetime=opens_datetime,
                status="open",
            )
        )
