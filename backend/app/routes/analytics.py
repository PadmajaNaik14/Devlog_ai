
from bson import ObjectId
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from app.database.dependencies import get_db
from app.middleware.auth_middleware import get_current_user

router = APIRouter()

TZ = ZoneInfo("Asia/Kolkata")


def get_user_journals(db: Database, user_id: str) -> list:
    return list(
        db["journals"].find({"user_id": user_id})
    )


def get_journal_dates(journals: list) -> list:
    """Convert journal timestamps to unique dates in IST."""
    dates = set()

    for journal in journals:
        created_at = journal.get("created_at")

        if not isinstance(created_at, datetime):
            continue

        # MongoDB commonly returns naive datetimes in UTC.
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        dates.add(created_at.astimezone(TZ).date())

    return sorted(dates)


def calculate_current_streak(dates: list) -> int:
    """
    Count consecutive journal days ending today or yesterday.
    Return zero if the most recent journal is older than yesterday.
    """
    if not dates:
        return 0

    date_set = set(dates)
    today = datetime.now(TZ).date()
    latest_date = max(date_set)

    # A journal yesterday keeps the streak active today.
    if latest_date < today - timedelta(days=1):
        return 0

    streak = 0
    day = latest_date

    while day in date_set:
        streak += 1
        day -= timedelta(days=1)

    return streak


def calculate_longest_streak(dates: list) -> int:
    """Find the maximum consecutive journal-day streak."""
    if not dates:
        return 0

    dates = sorted(set(dates))
    longest = 1
    current = 1

    for i in range(1, len(dates)):
        if dates[i] == dates[i - 1] + timedelta(days=1):
            current += 1
        else:
            current = 1

        longest = max(longest, current)

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
        raise HTTPException(
            status_code=400,
            detail="Month must be 1-12",
        )

    # Interpret requested month and year in IST.
    start_local = datetime(year, month, 1, tzinfo=TZ)

    if month == 12:
        end_local = datetime(year + 1, 1, 1, tzinfo=TZ)
    else:
        end_local = datetime(year, month + 1, 1, tzinfo=TZ)

    start = start_local.astimezone(timezone.utc)
    end = end_local.astimezone(timezone.utc)

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
    dates = get_journal_dates(journals)

    days = [
        day.day
        for day in dates
        if day.month == month and day.year == year
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

        if isinstance(created_at, datetime):
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

            month_name = created_at.astimezone(TZ).strftime("%b")
            months[month_name] += 1

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

        if not isinstance(created_at, datetime):
            continue

        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        day = str(created_at.astimezone(TZ).date())
        result[day] = result.get(day, 0) + 1

    return result


@router.get("/activity-calendar")
def activity_calendar(
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    user_id = current_user["user_id"]

    journals = get_user_journals(db, user_id)
    logins = list(
        db["login_activity"].find({"user_id": user_id})
    )

    # Get unique journal dates in IST.
    journal_days_set = set()

    for journal in journals:
        created_at = journal.get("created_at")

        if not isinstance(created_at, datetime):
            continue

        # Treat naive timestamps as UTC.
        if created_at.tzinfo is None:
            created_at = created_at.replace(
                tzinfo=timezone.utc
            )

        journal_day = str(
            created_at.astimezone(TZ).date()
        )

        journal_days_set.add(journal_day)

    journal_days = sorted(journal_days_set)

    # Get unique login dates in IST.
    login_days_set = set()

    for login in logins:
        created_at = (
            login.get("created_at")
            or login.get("login_date")
        )

        if not isinstance(created_at, datetime):
            continue

        # Treat naive timestamps as UTC.
        if created_at.tzinfo is None:
            created_at = created_at.replace(
                tzinfo=timezone.utc
            )

        login_day = str(
            created_at.astimezone(TZ).date()
        )

        login_days_set.add(login_day)

    login_days = sorted(login_days_set)

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
        user = db["users"].find_one({
            "_id": ObjectId(user_id)
        })

    return {
        "total_journals": len(journals),
        "current_streak": calculate_current_streak(dates),
        "longest_streak": calculate_longest_streak(dates),
        "ai_optimizations": (
            user.get("ai_optimizations", 0) if user else 0
        ),
    }
