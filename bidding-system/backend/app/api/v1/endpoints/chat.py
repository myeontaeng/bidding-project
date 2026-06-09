import re
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.announcement import Announcement

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


def _now() -> datetime:
    kst = timezone(timedelta(hours=9))
    return datetime.now(kst).replace(tzinfo=None)


def _parse_intent_simple(msg: str) -> dict:
    """키워드 기반 intent 파싱 (OpenAI 없을 때 fallback)"""
    msg_lower = msg.lower()
    filters: dict = {}

    categories = {
        "IT서비스": "IT서비스", "소프트웨어": "소프트웨어", "건설": "건설",
        "용역": "용역", "물품구매": "물품구매", "물품": "물품구매",
        "시설공사": "시설공사", "시설": "시설공사",
    }
    for kw, cat in categories.items():
        if kw in msg_lower:
            filters["category"] = cat
            break

    m = re.search(r"(\d+(?:\.\d+)?)\s*억\s*(이상|이하|미만|초과)?", msg)
    if m:
        amount = float(m.group(1)) * 1e8
        qual = m.group(2) or "이상"
        if qual in ("이상", "초과"):
            filters["budget_min"] = amount
        else:
            filters["budget_max"] = amount

    if any(w in msg_lower for w in ["마감임박", "급한", "이번 주", "긴급", "빨리"]):
        filters["imminent"] = True

    filters["status"] = "open"
    return filters


async def _query_announcements(db: AsyncSession, filters: dict) -> list[dict]:
    now = _now()
    conds = [Announcement.status == "open"]
    conds.append(or_(Announcement.deadline.is_(None), Announcement.deadline >= now))

    if filters.get("category"):
        conds.append(Announcement.category == filters["category"])
    if filters.get("budget_min"):
        conds.append(Announcement.budget >= filters["budget_min"])
    if filters.get("budget_max"):
        conds.append(Announcement.budget <= filters["budget_max"])
    if filters.get("imminent"):
        conds.append(Announcement.deadline <= now + timedelta(days=7))
        conds.append(Announcement.deadline >= now)

    rows = list((await db.execute(
        select(Announcement)
        .where(and_(*conds))
        .order_by(Announcement.deadline.asc().nullslast())
        .limit(5)
    )).scalars().all())

    from app.services.announcement import _calc_dday
    return [
        {
            "id": r.id,
            "title": r.title,
            "organization": r.organization,
            "budget": r.budget,
            "deadline": r.deadline.isoformat() if r.deadline else None,
            "category": r.category,
            "dday": _calc_dday(r.deadline),
        }
        for r in rows
    ]


def _build_response_text(filters: dict, results: list, original: str) -> str:
    if not results:
        return "조건에 맞는 공고를 찾지 못했습니다. 검색 조건을 넓혀보시겠어요?"
    applied = []
    if filters.get("category"):
        applied.append(f"업종: {filters['category']}")
    if filters.get("budget_min"):
        applied.append(f"예산 {filters['budget_min']/1e8:.0f}억원 이상")
    if filters.get("budget_max"):
        applied.append(f"예산 {filters['budget_max']/1e8:.0f}억원 이하")
    if filters.get("imminent"):
        applied.append("이번 주 마감")
    cond_str = ("  조건: " + ", ".join(applied)) if applied else ""
    return f"{len(results)}건 찾았습니다.{cond_str}"


@router.post("")
async def chat(body: ChatRequest, db: AsyncSession = Depends(get_db)):
    from app.core.config import settings

    message = body.message.strip()
    if not message:
        return {"message": "메시지를 입력해주세요.", "announcements": [], "filter_applied": {}, "ai_used": False}

    filters: dict = {}
    ai_used = False

    if settings.OPENAI_API_KEY:
        try:
            import json as _json
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            resp = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": (
                        "공공입찰 공고 검색 어시스턴트. 사용자 질문에서 검색 조건을 추출해 JSON 반환.\n"
                        "필드(없으면 생략): category(IT서비스|소프트웨어|건설|용역|물품구매|시설공사), "
                        "budget_min(숫자,원단위), budget_max(숫자,원단위), imminent(bool)\n"
                        "JSON만 반환. 마크다운 코드블록 사용 금지."
                    )},
                    {"role": "user", "content": message},
                ],
                max_tokens=150,
            )
            raw = resp.choices[0].message.content.strip()
            filters = _json.loads(raw)
            ai_used = True
        except Exception:
            filters = _parse_intent_simple(message)
    else:
        filters = _parse_intent_simple(message)

    announcements = await _query_announcements(db, filters)
    return {
        "message": _build_response_text(filters, announcements, message),
        "announcements": announcements,
        "filter_applied": filters,
        "ai_used": ai_used,
    }
