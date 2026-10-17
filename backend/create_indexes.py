
from app.database.mongodb import db

print("Creating MongoDB indexes...")

# Prevent duplicate email addresses
db["users"].create_index("email", unique=True)

# Speed up journal listing by user and date
db["journals"].create_index([
    ("user_id", 1),
    ("created_at", -1)
])

# Speed up chat history retrieval
db["chat_messages"].create_index([
    ("user_id", 1),
    ("created_at", 1)
])

# Speed up login activity retrieval
db["login_activity"].create_index([
    ("user_id", 1),
    ("created_at", -1)
])

print("\nIndexes created successfully!")

for name in ["users", "journals", "chat_messages", "login_activity"]:
    print(f"\n{name} indexes:")
    for index in db[name].list_indexes():
        print(index)
