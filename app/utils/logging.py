import logging
from datetime import (
    datetime,
    timezone,
)

import psycopg2
from psycopg2 import sql
from utils.db import (
    DB_CONN_PARAMS,
    PROD_SCHEMA,
)


class DatabaseLogHandler(logging.Handler):
    def __init__(
        self,
        connection_params: dict,
        table_name: str = "log",
        schema_name: str = PROD_SCHEMA,
    ):
        super(DatabaseLogHandler, self).__init__()
        self.connection_params = connection_params
        self.table_name = table_name
        self.schema_name = schema_name
        self.create_table()

        self.insert_query = sql.SQL(
            "INSERT INTO {} (level, message, created_at) VALUES (%s, %s, %s);"
        ).format(sql.Identifier(self.schema_name + "." + self.table_name))

    def create_table(self):
        table_schema = sql.SQL(
            """
            CREATE TABLE IF NOT EXISTS {} (
                id SERIAL PRIMARY KEY,
                level TEXT,
                message TEXT,
                created_at TIMESTAMP
            )
        """
        ).format(sql.Identifier(self.schema_name + "." + self.table_name))

        with psycopg2.connect(**self.connection_params) as conn:
            conn.cursor().execute(table_schema)

    def emit(self, record):
        created_datetime = datetime.fromtimestamp(record.created, timezone.utc)
        with psycopg2.connect(**self.connection_params) as conn:
            conn.cursor().execute(
                self.insert_query,
                (record.levelname, record.msg, created_datetime),
            )


LOGGER: logging.Logger = logging.getLogger("database_logger")
LOGGER.setLevel(logging.INFO)
log_handler = DatabaseLogHandler(DB_CONN_PARAMS)
LOGGER.addHandler(log_handler)
