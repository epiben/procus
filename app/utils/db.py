from dotenv import load_dotenv
import psycopg2
from contextlib import contextmanager

load_dotenv(".env")
DB_CONN_PARAMS: dict = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "postgres",
    "host": "db",
    "port": "5432",
}

TEST_DB_CONN_PARAMS: dict = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "postgres",
    "host": "db",
    "port": "6432"
}

PROD_SCHEMA: str = "prod"

@contextmanager
def get_db(conn_params: dict[str, str]):
    conn = None
    try:
        # Connect to your database
        conn = psycopg2.connect(**conn_params)
        yield conn
    finally:
        if conn is not None:
            conn.close()

def get_prod_db():
    return get_db(DB_CONN_PARAMS)

def get_test_db():
    return get_db(TEST_DB_CONN_PARAMS)
