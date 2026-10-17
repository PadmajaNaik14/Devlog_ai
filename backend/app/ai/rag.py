
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


def retrieve_context(query, user_id):
    """Retrieve relevant journal documents for one user."""

    embedding = generate_embedding(query)

    results = collection.query(
        query_embeddings=[embedding],
        n_results=3,
        where={
            "user_id": str(user_id),
        },
        include=["documents", "metadatas", "distances"],
    )

    return results
