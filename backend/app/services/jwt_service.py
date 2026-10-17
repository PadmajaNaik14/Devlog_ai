
from datetime import datetime, timedelta, timezone
import os

from dotenv import load_dotenv
from jose import JWTError, jwt

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

if not SECRET_KEY:
    raise ValueError("SECRET_KEY not found in .env")


def create_access_token(user_id: str) -> str:
    payload = {
        "user_id": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(days=1),
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def verify_token(token: str):
    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
    except JWTError:
        return None
