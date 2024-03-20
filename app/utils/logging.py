import logging

from fastapi import Depends
from sqlalchemy.engine import Engine
from utils.db import (
    make_engine,
    make_session,
)
from utils.orm import Log


class DatabaseLogHandler(logging.Handler):
    def __init__(
        self,
        engine: Engine = Depends(make_engine),
    ):
        super(DatabaseLogHandler, self).__init__()
        self.engine = engine

    def emit(self, record):
        with make_session(self.engine) as session:
            log = Log(
                level=record.levelname,
                message=record.msg,
            )
            session.add(log)
            session.commit()


LOGGER: logging.Logger = logging.getLogger("database_logger")
LOGGER.setLevel(logging.INFO)
log_handler = DatabaseLogHandler()
LOGGER.addHandler(log_handler)
