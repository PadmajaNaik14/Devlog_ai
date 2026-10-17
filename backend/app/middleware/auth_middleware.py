
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.jwt_service import verify_token

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing token")

    payload = verify_token(credentials.credentials)

    if not payload or not payload.get("user_id"):
        raise HTTPException(status_code=401, detail="Invalid token")

    return {"user_id": str(payload["user_id"])}
