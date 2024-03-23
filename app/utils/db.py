from contextlib import contextmanager
from typing import (
    Final,
    Iterator,
    NamedTuple,
    Optional,
)

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session as SQLAlchemySession

load_dotenv(".env")

with open("/run/secrets/postgres_password", "r") as f:
    POSTGRES_PASSWORD: str = f.readline()

DB_CONN_PARAMS: dict = {
    "dbname": "postgres",
    "user": "postgres",
    "password": POSTGRES_PASSWORD,
    "host": "db",
    "port": "5432",
}

DB_CONN_PARAMS_TEST: dict = {
    "dbname": "postgres",
    "user": "postgres",
    "password": POSTGRES_PASSWORD,
    "host": "db",
    "port": "6432",
}

PROD_SCHEMA: Final[str] = "prod"


class ConnectionDetails(NamedTuple):
    """A simple type for storing connection details"""

    host: str
    dbms: Optional[str] = "postgresql"
    dbname: Optional[str] = ""
    port: Optional[int] = 5432
    user: Optional[str] = ""
    password: Optional[str] = ""
    schema: Optional[str] = ""


def _create_engine(
    user: Optional[str] = "postgres",
    password: Optional[str] = "",
    host: Optional[str] = "localhost",
    dbms: Optional[str] = "postgresql",
    dbname: Optional[str] = "postgres",
    port: Optional[int] = 5432,
    schema: Optional[str] = None,  # we do this in ProcusBase
    **kwargs,
) -> Engine:
    """Create a Postgres database engine based on connection details"""
    url = f"{dbms}://{user}:{password}@{host}:{port}/{dbname}"
    return create_engine(url)


def make_engine() -> Engine:
    cnxn = ConnectionDetails(**DB_CONN_PARAMS)
    return _create_engine(**cnxn._asdict())


def make_engine_test() -> Engine:
    cnxn = ConnectionDetails(**DB_CONN_PARAMS_TEST)
    return _create_engine(**cnxn._asdict())


@contextmanager
def make_session(engine: Engine) -> Iterator[SQLAlchemySession]:
    """Provide a transactional scope around a series of operations."""

    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
        session.commit()
    except AttributeError:
        session.rollback()
    finally:
        session.close()
