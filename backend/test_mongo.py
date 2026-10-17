
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

uri = os.getenv("MONGODB_URI")
database_name = os.getenv("MONGODB_DATABASE", "devlog_ai")

if not uri:
    raise RuntimeError("MONGODB_URI is missing from .env")

client = MongoClient(
    uri,
    serverSelectionTimeoutMS=10000,
)

try:
    client.admin.command("ping")
    print("MongoDB Atlas connection successful!")
    print("Database:", database_name)
except Exception as e:
    print("MongoDB connection failed:", e)
finally:
    client.close()
