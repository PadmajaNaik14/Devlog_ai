
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from app.database.dependencies import get_db
from app.schemas.journal_schema import CreateJournal
from app.models.journal import (
    create_journal_document,
    serialize_journal,
)
from app.ai.rag import (
    store_journal,
    update_journal_embedding,
    delete_journal_embedding,
)
from app.middleware.auth_middleware import get_current_user

router = APIRouter()


def validate_journal_id(journal_id: str) -> ObjectId:
    if not ObjectId.is_valid(journal_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid journal ID",
        )

    return ObjectId(journal_id)


@router.get("/")
def get_journals(
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    journals = list(
        db["journals"].find(
            {"user_id": current_user["user_id"]}
        ).sort("created_at", -1)
    )

    return [serialize_journal(j) for j in journals]


@router.get("/{journal_id}")
def get_journal(
    journal_id: str,
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    journal_oid = validate_journal_id(journal_id)

    journal = db["journals"].find_one({
        "_id": journal_oid,
        "user_id": current_user["user_id"],
    })

    if not journal:
        raise HTTPException(
            status_code=404,
            detail="Journal not found",
        )

    return serialize_journal(journal)


@router.post("/")
def create_journal(
    journal: CreateJournal,
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    document = create_journal_document(
        title=journal.title,
        content=journal.content,
        user_id=current_user["user_id"],
    )

    result = db["journals"].insert_one(document)

    try:
        store_journal(
            str(result.inserted_id),
            current_user["user_id"],
            journal.content,
        )
    except Exception:
        # Keep the journal saved even if vector indexing fails.
        # The RAG indexing can be retried separately.
        pass

    return {
        "message": "Journal Created",
        "id": str(result.inserted_id),
    }


@router.put("/{journal_id}")
def update_journal(
    journal_id: str,
    journal: CreateJournal,
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    journal_oid = validate_journal_id(journal_id)

    result = db["journals"].update_one(
        {
            "_id": journal_oid,
            "user_id": current_user["user_id"],
        },
        {
            "$set": {
                "title": journal.title,
                "content": journal.content,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Journal not found",
        )
    updated = db["journals"].find_one({
        "_id": journal_oid,
        "user_id": current_user["user_id"],
    })

    update_journal_embedding(
        str(updated["_id"]),
        current_user["user_id"],
        updated["content"],
    )

    return {"message": "Updated"}


@router.delete("/{journal_id}")
def delete_journal(
    journal_id: str,
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    journal_oid = validate_journal_id(journal_id)

    result = db["journals"].delete_one({
        "_id": journal_oid,
        "user_id": current_user["user_id"],
    })

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Journal not found",
        )
    delete_journal_embedding(
        str(journal_oid),
        current_user["user_id"],
    )

    return {"message": "Deleted"}
