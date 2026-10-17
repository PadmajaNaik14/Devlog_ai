
import os

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "devlog_ai")

if not MONGODB_URI:
    raise ValueError("MONGODB_URI not found in .env")

client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=10000,
)

db: Database = client[MONGODB_DATABASE]


def get_database() -> Database:
    return db


def close_mongodb_connection() -> None:
    client.close()
