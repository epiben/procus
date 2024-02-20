from datetime import datetime, timezone
from dotenv import load_dotenv
from psycopg2 import sql
import logging
import os
import psycopg2

load_dotenv(".env")

def document_sms(
        connection,
        phone_number: str,
        message_body: str,
        direction: str
        ) -> None:
    timestamp = datetime.now(timezone.utc)
    connection.cursor().execute(
        """
        INSERT INTO messages 
            (sent_datetime, phone_number, message_body, direction)
        VALUES (%s, %s, %s, %s);
        """,
        (timestamp, phone_number, message_body, direction)
    )

class DatabaseLogHandler(logging.Handler):
    def __init__(self, connection_params, table_name="log"):
        super(DatabaseLogHandler, self).__init__()
        self.connection_params = connection_params
        self.table_name = table_name
        self.create_table()

        self.insert_query = sql.SQL(
            "INSERT INTO {} (level, message, created_at) VALUES (%s, %s, %s);"
        ).format(sql.Identifier(self.table_name))

    def create_table(self):
        table_schema = sql.SQL("""
            CREATE TABLE IF NOT EXISTS {} (
                id SERIAL PRIMARY KEY,
                level TEXT,
                message TEXT,
                created_at TIMESTAMP
            )
        """).format(sql.Identifier(self.table_name))

        with psycopg2.connect(**self.connection_params) as conn:
            conn.cursor().execute(table_schema)

    def emit(self, record):
        created_timestamp = datetime.fromtimestamp(record.created, timezone.utc)
        with psycopg2.connect(**self.connection_params) as conn:
            conn.cursor().execute(
                self.insert_query, 
                (record.levelname, record.msg, created_timestamp)
            )

DB_CONN_PARAMS = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "postgres",
    "host": "db",
    "port": "5432"
}
