
from collections.abc import Generator

from pymongo.database import Database

from app.database.mongodb import get_database


def get_db() -> Generator[Database, None, None]:
    yield get_database()
