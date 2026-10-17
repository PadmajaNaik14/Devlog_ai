from bson import ObjectId
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.database.dependencies import get_db
from app.middleware.auth_middleware import get_current_user

router = APIRouter()


def get_user_journals(db: Database, user_id: str) -> list:
    return list(
        db["journals"].find({"user_id": user_id})
    )


def get_journal_dates(journals: list) -> list:
    dates = set()

    for journal in journals:
        created_at = journal.get("created_at")

        if created_at:
            if created_at.tzinfo is not None:
                created_at = created_at.astimezone(timezone.utc)

            dates.add(created_at.date())

    return sorted(dates)


def calculate_current_streak(dates: list) -> int:
    date_set = set(dates)
    today = datetime.now(timezone.utc).date()

    # Preserve the original behavior: streaks require activity today.
    if today not in date_set:
        return 0

    streak = 0
    day = today

    while day in date_set:
        streak += 1
        day -= timedelta(days=1)

    return streak


def calculate_longest_streak(dates: list) -> int:
    if not dates:
        return 0

    longest = 1
    current = 1

    for i in range(1, len(dates)):
        if dates[i] == dates[i - 1] + timedelta(days=1):
            current += 1
            longest = max(longest, current)
        else:
            current = 1

    return longest


@router.get("/")
def analytics_home():
    return {"message": "Analytics Route Working"}


@router.get("/month")
def get_month_journals(
    month: int,
    year: int,
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    if month < 1 or month > 12:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Month must be 1-12")

    start = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc)

    journals = list(
        db["journals"].find({
            "user_id": current_user["user_id"],
            "created_at": {"$gte": start, "$lt": end},
        }).sort("created_at", -1)
    )

    return [
        {
            "id": str(j["_id"]),
            "title": j.get("title", ""),
            "content": j.get("content", ""),
            "created_at": j.get("created_at"),
            "updated_at": j.get("updated_at"),
            "user_id": j.get("user_id"),
        }
        for j in journals
    ]


@router.get("/calendar")
def calendar_view(
    month: int,
    year: int,
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    journals = get_user_journals(db, current_user["user_id"])

    days = [
        j["created_at"].day
        for j in journals
        if j.get("created_at")
        and j["created_at"].month == month
        and j["created_at"].year == year
    ]

    return {"days": days}


@router.get("/total")
def total_journals(
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    count = db["journals"].count_documents({
        "user_id": current_user["user_id"]
    })

    return {"total_journals": count}


@router.get("/monthly-count")
def monthly_count(
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    months = {
        "Jan": 0, "Feb": 0, "Mar": 0, "Apr": 0,
        "May": 0, "Jun": 0, "Jul": 0, "Aug": 0,
        "Sep": 0, "Oct": 0, "Nov": 0, "Dec": 0,
    }

    journals = get_user_journals(db, current_user["user_id"])

    for journal in journals:
        created_at = journal.get("created_at")
        if created_at:
            months[created_at.strftime("%b")] += 1

    return [
        {"month": name, "journals": count}
        for name, count in months.items()
    ]


@router.get("/streak")
def current_streak(
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    journals = get_user_journals(db, current_user["user_id"])
    dates = get_journal_dates(journals)

    return {"streak": calculate_current_streak(dates)}


@router.get("/longest-streak")
def longest_streak(
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    journals = get_user_journals(db, current_user["user_id"])
    dates = get_journal_dates(journals)

    return {"longest_streak": calculate_longest_streak(dates)}


@router.get("/heatmap")
def heatmap(
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    journals = get_user_journals(db, current_user["user_id"])
    result = {}

    for journal in journals:
        created_at = journal.get("created_at")
        if created_at:
            day = str(created_at.date())
            result[day] = result.get(day, 0) + 1

    return result


@router.get("/activity-calendar")
def activity_calendar(
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    user_id = current_user["user_id"]

    journals = get_user_journals(db, user_id)
    logins = list(db["login_activity"].find({"user_id": user_id}))

    journal_days = sorted({
        str(j["created_at"].date())
        for j in journals
        if j.get("created_at")
    })

    login_days = sorted({
        str(
            (login.get("created_at") or login.get("login_date")).date()
        )
        for login in logins
        if login.get("created_at") or login.get("login_date")
    })

    return {
        "journal_days": journal_days,
        "login_days": login_days,
    }


@router.get("/dashboard")
def dashboard(
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    user_id = current_user["user_id"]
    journals = get_user_journals(db, user_id)
    dates = get_journal_dates(journals)

    user = None

    if ObjectId.is_valid(user_id):
        user = db["users"].find_one({"_id": ObjectId(user_id)})

    return {
        "total_journals": len(journals),
        "current_streak": calculate_current_streak(dates),
        "longest_streak": calculate_longest_streak(dates),
        "ai_optimizations": user.get("ai_optimizations", 0) if user else 0,
    }
