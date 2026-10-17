
from app.ai.embeddings import generate_embedding
from app.ai.vector_store import collection


def store_journal(journal_id, user_id, content):
    """Insert or update a journal in ChromaDB."""

    journal_id = str(journal_id)
    user_id = str(user_id)

    embedding = generate_embedding(content)

    collection.upsert(
        ids=[journal_id],
        embeddings=[embedding],
        documents=[content],
        metadatas=[
            {
                "user_id": user_id,
                "journal_id": journal_id,
            }
        ],
    )


def update_journal_embedding(journal_id, user_id, content):
    """Refresh a journal's embedding after its content changes."""

    store_journal(journal_id, user_id, content)


def delete_journal_embedding(journal_id, user_id):
    """Delete a journal's vector only if it belongs to the user."""

    collection.delete(
        ids=[str(journal_id)],
        where={
            "user_id": str(user_id),
        },
    )


def retrieve_context(query, user_id, db=None):
    """Retrieve relevant journals from ChromaDB, with MongoDB fallback."""

    user_id = str(user_id)
    docs = []
    metas = []
    distances = []

    # Try semantic retrieval first.
    try:
        embedding = generate_embedding(query)

        results = collection.query(
            query_embeddings=[embedding],
            n_results=5,
            where={"user_id": user_id},
            include=["documents", "metadatas", "distances"],
        )

        docs = (results.get("documents") or [[]])[0] or []
        metas = (results.get("metadatas") or [[]])[0] or []
        distances = (results.get("distances") or [[]])[0] or []

    except Exception as e:
        print(f"ChromaDB retrieval failed: {type(e).__name__}")

    # If semantic search finds nothing, use this user's MongoDB journals.
    if not docs and db is not None:
        try:
            journals = list(
                db["journals"]
                .find({"user_id": user_id})
                .sort("created_at", -1)
                .limit(10)
            )

            docs = [
                f"Title: {j.get('title', 'Untitled')}\n"
                f"Content: {j.get('content', '')}"
                for j in journals
                if j.get("content")
            ]

            metas = [
                {
                    "user_id": user_id,
                    "journal_id": str(j["_id"]),
                }
                for j in journals
                if j.get("content")
            ]

        except Exception as e:
            print(f"MongoDB journal fallback failed: {type(e).__name__}")

    return {
        "documents": [docs],
        "metadatas": [metas],
        "distances": [distances],
    }

