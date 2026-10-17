
from datetime import datetime, timezone

from bson import ObjectId


def create_journal_document(
    title: str,
    content: str,
    user_id: str,
) -> dict:
    now = datetime.now(timezone.utc)

    return {
        "title": title,
        "content": content,
        "created_at": now,
        "updated_at": now,
        "user_id": user_id,
    }


def serialize_journal(journal: dict) -> dict:
    return {
        "id": str(journal["_id"]),
        "title": journal.get("title", ""),
        "content": journal.get("content", ""),
        "created_at": journal.get("created_at"),
        "updated_at": journal.get("updated_at"),
        "user_id": journal.get("user_id"),
    }


def is_valid_journal_id(journal_id: str) -> bool:
    return ObjectId.is_valid(journal_id)
