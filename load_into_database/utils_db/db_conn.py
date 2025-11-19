import psycopg
from psycopg.rows import dict_row

def get_conn():
    # psycopg[binary] 自带 libpq，不需要额外 client_encoding 选项
    conn = psycopg.connect(
        dbname="Folktales-AIGC",
        user="postgres",
        password="850101",
        host="localhost",
        port=5432
    )
    return conn

def get_cursor(conn):
    return conn.cursor(row_factory=dict_row)
