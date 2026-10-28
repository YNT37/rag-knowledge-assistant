import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env", override=False)

database_url = URL.create(
    drivername="mysql+pymysql",
    username=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.environ["DB_HOST"],
    port=int(os.environ["DB_PORT"]),
    database=os.environ["DB_NAME"],
    query={"charset": "utf8mb4"},
)

engine = create_engine(database_url)


with engine.connect() as connection:
    statement = text("SELECT DATABASE(), CURRENT_USER(), 1")
    result = connection.execute(statement)
    row = result.one()
    print(row)