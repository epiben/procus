import datetime
import enum

from sqlalchemy import (
    Column,
    Enum,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)
from sqlalchemy.sql import func
from sqlalchemy.types import (
    Boolean,
    DateTime,
    Integer,
    String,
    Text,
)
from utils.db import PROD_SCHEMA


class ProcusBase(DeclarativeBase):
    __abstract__ = True
    __table_args__ = {"schema": PROD_SCHEMA}


class Iteration(ProcusBase):
    __tablename__ = "iterations"

    iteration_id: Mapped[int] = mapped_column(
        Integer(), primary_key=True, nullable=False
    )
    instrument_id: Mapped[int] = mapped_column(Integer(), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(24), nullable=False)
    message_body: Mapped[str] = mapped_column(String(720), nullable=False)
    is_open: Mapped[bool] = mapped_column(Boolean, nullable=False)
    opens_datetime: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_datetime: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_by: Mapped[str] = mapped_column(String(40), nullable=False)

    def __repr__(self) -> str:
        return (
            f"Iteration(id={self.iteration_id!r}, "
            f"Phone number={self.phone_number!r}, "
            f"Is open={self.is_open!r})"
        )


class Response(ProcusBase):
    __tablename__ = "responses"

    response_id: Mapped[int] = Column(Integer, primary_key=True)
    phone_number: Mapped[str] = Column(Text, nullable=True)
    item_id: Mapped[int] = Column(Integer, nullable=True)
    item_text: Mapped[str] = Column(Text, nullable=True)
    opens_datetime: Mapped[DateTime] = Column(
        DateTime(timezone=True), nullable=True
    )
    response: Mapped[int] = Column(Integer, nullable=True)
    status: Mapped[str] = Column(Text, nullable=True)
    created_datetime: Mapped[datetime.datetime] = Column(
        DateTime(timezone=True), default=func.now(), nullable=True
    )
    updated_by: Mapped[str] = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"""<Response(response_id={self.response_id},
        phone_number={self.phone_number},
        item_id={self.item_id},
        item_text={self.item_text},
        opens_datetime={self.opens_datetime},
        response={self.response},
        status={self.status},
        created_datetime={self.created_datetime},
        updated_by={self.updated_by})>
        """


class Recipient(ProcusBase):
    __tablename__ = "recipients"

    recipient_id: Mapped[int] = Column(
        Integer, primary_key=True, nullable=False
    )
    phone_number: Mapped[str] = Column(Text, nullable=False)
    full_name: Mapped[str] = Column(Text, nullable=False)
    created_datetime: Mapped[datetime.datetime] = Column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"""<Recipient(recipient_id={self.recipient_id},
        phone_number={self.phone_number},
        created_datetime={self.created_datetime})>"""


class DirectionEnum(enum.Enum):
    inbound = "inbound"
    outbound = "outbound"


class Message(ProcusBase):
    __tablename__ = "messages"

    message_id: Mapped[int] = Column(Integer, primary_key=True, nullable=False)
    sent_datetime: Mapped[datetime.datetime] = Column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    phone_number: Mapped[str] = Column(Text, nullable=False)
    message_body: Mapped[str] = Column(Text, nullable=False)
    direction: Mapped[str] = Column(Enum(DirectionEnum))


class Item(ProcusBase):
    __tablename__ = "items"

    item_id: Mapped[int] = Column(Integer, primary_key=True, nullable=False)
    instrument_id: Mapped[int] = Column(Integer, nullable=False)
    item_text: Mapped[str] = Column(Text, nullable=False)
    created_datetime: Mapped[datetime.datetime] = Column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_by: Mapped[str] = Column(Text, nullable=False)


class Instrument(ProcusBase):
    __tablename__ = "instruments"

    instrument_id: Mapped[int] = Column(
        Integer, primary_key=True, nullable=False
    )
    instrument_name: Mapped[str] = Column(Text, nullable=False)
    is_active: Mapped[bool] = Column(Boolean, nullable=False)
    created_datetime: Mapped[datetime.datetime] = Column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_by: Mapped[str] = Column(Text, nullable=False)


class Log(ProcusBase):
    __tablename__ = "log"

    id: Mapped[int] = Column(Integer, primary_key=True)
    level: Mapped[str] = Column(Text, nullable=False)
    message: Mapped[str] = Column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = Column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
