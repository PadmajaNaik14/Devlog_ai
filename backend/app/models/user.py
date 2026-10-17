
from datetime import datetime, timezone

from bson import ObjectId


def create_user_document(
    name: str,
    email: str,
    password_hash: str,
) -> dict:
    return {
        "name": name,
        "email": email,
        "password_hash": password_hash,
        "created_at": datetime.now(timezone.utc),
        "ai_optimizations": 0,
    }


def serialize_user(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "created_at": user["created_at"],
        "ai_optimizations": user.get("ai_optimizations", 0),
    }


def is_valid_user_id(user_id: str) -> bool:
    return ObjectId.is_valid(user_id)
