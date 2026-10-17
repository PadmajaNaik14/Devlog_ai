
from app.ai.vector_store import collection

journal_id = input("Enter the journal ID: ").strip()
user_id = input("Enter your user ID: ").strip()

result = collection.get(
    ids=[journal_id],
    include=["documents", "metadatas"]
)

if not result["ids"]:
    print("FAIL: No embedding found for this journal.")
else:
    metadata = result["metadatas"][0]
    document = result["documents"][0]

    print("Embedding record found!")
    print("Journal ID:", result["ids"][0])
    print("Stored user ID:", metadata.get("user_id"))
    print("Stored document:", document)

    if metadata.get("user_id") == user_id:
        print("PASS: Embedding belongs to the correct user.")
    else:
        print("FAIL: User ID does not match.")
