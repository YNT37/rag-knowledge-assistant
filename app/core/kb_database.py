import os
from _collections_abc import Iterator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session


PRPJECT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=PRPJECT_DIR / ".env", override=False)

database_url = URL.create(
    drivername="mysql+pymysql",
    username=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.environ["DB_HOST"],
    port=int(os.environ["DB_PORT"]),
    database=os.environ["DB_NAME"],
    query={"charset": "utf8mb4"},
)

engine = create_engine(database_url, pool_pre_ping=True)

DOCUMENTS_DIR = Path(
    os.getenv("KB_DOCUMENTS_DIR", str(PRPJECT_DIR / "practice" / "documents"))
)
if not DOCUMENTS_DIR.is_absolute():
    raise RuntimeError("KB_DOCUMENTS_DIR必须为绝对路径")


def get_kb_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
