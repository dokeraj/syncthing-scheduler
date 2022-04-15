import sqlite3
from dataclasses import dataclass
from sqlite3 import Error
import util


@dataclass
class ApiResponse:
    code: int
    msg: str
    timestamp: str


def init_db(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        conn.execute("DROP TABLE IF EXISTS LAST_STATUS;")

        conn.execute('''CREATE TABLE IF NOT EXISTS LAST_STATUS
                     (ID     INT          NOT NULL,
                     CODE            INT     NOT NULL,
                     LAST_RESPONSE        CHAR(1000),
                     TIMESTAMP            CHAR(100)     NOT NULL);''')

        conn.commit()
        print(f"Successfully initialized sqlite db: {sqlite3.version}")
    except Error as e:
        print(f"Error initializing sqlite: {e}")
    finally:
        if conn:
            conn.close()
        update_db(200, "Initialized - waiting for first checks", util.getCurrentDateTime())


def update_db(code: int, msg: str, timestamp: str):
    conn = sqlite3.connect(r"/sqldb/nova.db")
    conn.execute(
        f"""INSERT OR IGNORE INTO LAST_STATUS (ID,CODE,LAST_RESPONSE,TIMESTAMP) VALUES (1, {code}, \'{msg}\', \'{timestamp}\')""")
    conn.execute(
        f"UPDATE LAST_STATUS SET LAST_RESPONSE=\'{msg}\', CODE = {code}, TIMESTAMP = \'{timestamp}\' WHERE ID=1; ")

    conn.commit()
    conn.close()


def get_from_db():
    lastResp = None
    conn = sqlite3.connect(r"/sqldb/nova.db")
    cur = conn.cursor()
    cur.execute(f"""SELECT * FROM LAST_STATUS;""")
    records = cur.fetchall()
    row = records[0]
    if records:
        lastResp = ApiResponse(code=row[1], msg=row[2], timestamp=row[3])

    conn.close()

    return lastResp
