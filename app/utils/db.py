from dotenv import load_dotenv

load_dotenv(".env")

DB_CONN_PARAMS: dict = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "postgres",
    "host": "db",
    "port": "5432",
}
