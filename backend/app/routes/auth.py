
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from app.schemas.user_schema import RegisterUser
from app.schemas.login_schema import LoginUser
from app.database.dependencies import get_db
from app.services.auth_service import hash_password, verify_password
from app.services.jwt_service import create_access_token
from app.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.get("/")
def test():
    return {"message": "Auth Route Working"}


@router.post("/register")
def register_user(
    user: RegisterUser,
    db: Database = Depends(get_db),
):
    existing_user = db["users"].find_one(
        {"email": user.email}
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    new_user = {
        "name": user.name,
        "email": user.email,
        "password_hash": hash_password(user.password),
        "created_at": datetime.now(timezone.utc),
        "ai_optimizations": 0,
    }

    result = db["users"].insert_one(new_user)

    return {
        "message": "User Registered Successfully",
        "id": str(result.inserted_id),
    }


@router.post("/login")
def login_user(
    user: LoginUser,
    db: Database = Depends(get_db),
):
    db_user = db["users"].find_one(
        {"email": user.email}
    )

    if not db_user:
        raise HTTPException(
            status_code=401,
            detail="Email not found",
        )

    valid = verify_password(
        user.password,
        db_user["password_hash"],
    )

    if not valid:
        raise HTTPException(
            status_code=401,
            detail="Incorrect password",
        )

    user_id = str(db_user["_id"])

    token = create_access_token(user_id)

    db["login_activity"].insert_one({
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc),
    })

    return {
        "access_token": token,
        "token_type": "bearer",
    }


@router.get("/me")
def get_me(
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    user_id = current_user["user_id"]

    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=401,
            detail="Invalid user ID",
        )

    user = db["users"].find_one({
        "_id": ObjectId(user_id)
    })

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
    }
