
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Request
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
        db=db,
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


def get_today_or_latest_journal(db: Database, user_id: str):
    """
    Return today's newest journal for this user.
    If none exists today, return their newest journal overall.
    Journal timestamps are assumed to be stored in UTC.
    """
    tz = ZoneInfo("Asia/Kolkata")
    now = datetime.now(tz)

    start_local = datetime.combine(
        now.date(),
        time.min,
        tzinfo=tz,
    )
    end_local = datetime.combine(
        now.date() + timedelta(days=1),
        time.min,
        tzinfo=tz,
    )

    start_utc = start_local.astimezone(timezone.utc).replace(
        tzinfo=None
    )
    end_utc = end_local.astimezone(timezone.utc).replace(
        tzinfo=None
    )

    journals = db["journals"]

    # First: newest journal created today.
    journal = journals.find_one(
        {
            "user_id": user_id,
            "created_at": {
                "$gte": start_utc,
                "$lt": end_utc,
            },
        },
        sort=[("created_at", -1)],
    )

    if journal:
        return journal

    # Fallback: newest journal from any date.
    return journals.find_one(
        {"user_id": user_id},
        sort=[("created_at", -1)],
    )


@router.post("/chat")
@limiter.limit("5/minute")
def chat(
    request: Request,
    chat_request: ChatRequest,
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    user_id = current_user["user_id"]
    question = chat_request.question.strip()
    now = datetime.now(timezone.utc)

    # Save the user's message.
    db["chat_messages"].insert_one({
        "user_id": user_id,
        "sender": "user",
        "message": question,
        "created_at": now,
    })

    normalized_question = question.lower()

    today_keywords = (
        "today",
        "today's",
        "todays",
    )

    requires_today_journal = any(
        keyword in normalized_question
        for keyword in today_keywords
    )

    if requires_today_journal:
        # Select today's journal, or fall back to the latest journal.
        journal = get_today_or_latest_journal(
            db,
            user_id,
        )

        if journal is None:
            answer = (
                "You haven't created any journal entries yet. "
                "Create your first journal to receive developer insights."
            )
        else:
            journal_content = (
                journal.get("content") or ""
            ).strip()

            journal_title = journal.get(
                "title",
                "Untitled",
            )
            journal_date = journal.get(
                "created_at",
                "Unknown",
            )

            if not journal_content:
                answer = (
                    "Your latest journal has no content to analyze. "
                    "Please add content to your journal and try again."
                )
            else:
                rag_context = (
                    "The following is the selected journal for "
                    "the user's request. Use this journal as the "
                    "primary source of truth. Do not claim older "
                    "work happened today.\n\n"
                    f"Title: {journal_title}\n"
                    f"Created at: {journal_date}\n\n"
                    f"Journal content:\n{journal_content}"
                )

                answer = chat_with_ai(
                    question,
                    rag_context,
                )

    else:
        # Preserve existing RAG behavior for ordinary chat.
        context = retrieve_context(
            question,
            user_id,
            db=db,
        )

        documents = context.get("documents") or [[]]
        rag_context = "\n\n".join(documents[0])

        answer = chat_with_ai(
            question,
            rag_context,
        )

    # Increment the counter once the request has produced an answer.
    db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$inc": {"ai_optimizations": 1}},
    )

    # Save the AI response.
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
