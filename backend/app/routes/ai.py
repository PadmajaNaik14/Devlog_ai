
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pymongo.database import Database

from app.database.dependencies import get_db
from app.ai.rag import retrieve_context
from app.ai.chat import chat_with_ai
from app.ai.optimizer import optimize_journal
from app.schemas.ai_schema import OptimizeRequest
from app.schemas.chat_schema import ChatRequest
from app.middleware.auth_middleware import get_current_user
from app.middleware.rate_limit import limiter
from bson import ObjectId
router = APIRouter()


@router.get("/")
def test():
    return {"message": "AI Route Working"}


@router.get("/search")
@limiter.limit("5/minute")
def search(
    request: Request,
    query: str,
    current_user=Depends(get_current_user),
):
    return retrieve_context(
        query,
        current_user["user_id"],
    )


@router.post("/optimize")
@limiter.limit("5/minute")
def optimize(
    request: Request,
    optimize_request: OptimizeRequest,
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    user_id = current_user["user_id"]

    context = retrieve_context(
        optimize_request.content,
        user_id,
    )

    documents = context.get("documents") or [[]]
    rag_context = "\n".join(documents[0])

    optimized = optimize_journal(
        optimize_request.content,
        rag_context,
    )

    db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$inc": {"ai_optimizations": 1}},
    )

    return {"optimized": optimized}


@router.post("/chat")
@limiter.limit("5/minute")
def chat(
    request: Request,
    chat_request: ChatRequest,
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    user_id = current_user["user_id"]
    now = datetime.now(timezone.utc)

    db["chat_messages"].insert_one({
        "user_id": user_id,
        "sender": "user",
        "message": chat_request.question,
        "created_at": now,
    })

    context = retrieve_context(
        chat_request.question,
        user_id,
    )

    documents = context.get("documents") or [[]]
    rag_context = "\n\n".join(documents[0])

    answer = chat_with_ai(
        chat_request.question,
        rag_context,
    )

    db["chat_messages"].insert_one({
        "user_id": user_id,
        "sender": "ai",
        "message": answer,
        "created_at": datetime.now(timezone.utc),
    })

    return {"answer": answer}


@router.get("/chat/history")
def get_chat_history(
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    history = list(
        db["chat_messages"]
        .find({"user_id": current_user["user_id"]})
        .sort("created_at", 1)
    )

    return [
        {
            "id": str(message["_id"]),
            "user_id": message["user_id"],
            "sender": message["sender"],
            "message": message["message"],
            "created_at": message["created_at"],
        }
        for message in history
    ]


@router.delete("/chat/history")
def clear_chat(
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result = db["chat_messages"].delete_many({
        "user_id": current_user["user_id"]
    })

    return {
        "message": "Chat Cleared",
        "deleted_count": result.deleted_count,
    }
