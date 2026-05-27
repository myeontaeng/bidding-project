import asyncio
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.schemas.announcement import AnnouncementFilter, AnnouncementRead
from app.services.announcement import get_announcements, _calc_dday
from app.services.scheduler import _run_crawl

router = APIRouter(prefix="/announcements", tags=["announcements"])


@router.get("", response_model=list[AnnouncementRead])
async def list_announcements(
    response: Response,
    keyword: str | None = Query(None),
    category: str | None = Query(None),
    region: str | None = Query(None),
    organization: str | None = Query(None),
    budget_min: float | None = Query(None),
    budget_max: float | None = Query(None),
    status: str | None = Query("open"),
    deadline_before: str | None = Query(None),  # YYYY-MM-DD
    deadline_after: str | None = Query(None),   # YYYY-MM-DD
    sort_by: str = Query("deadline"),           # deadline | published_at | budget_desc | budget_asc
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime as _dt
    def _parse_date(s: str | None, end_of_day: bool = False):
        if not s:
            return None
        try:
            d = _dt.strptime(s, "%Y-%m-%d")
            return d.replace(hour=23, minute=59, second=59) if end_of_day else d
        except ValueError:
            return None

    f = AnnouncementFilter(
        keyword=keyword, category=category, region=region,
        organization=organization, budget_min=budget_min,
        budget_max=budget_max, status=status, page=page, size=size,
        deadline_before=_parse_date(deadline_before, end_of_day=True),
        deadline_after=_parse_date(deadline_after),
        sort_by=sort_by,
    )
    anns, total = await get_announcements(db, f)
    response.headers["X-Total-Count"] = str(total)

    result = []
    for ann in anns:
        data = AnnouncementRead.model_validate(ann)
        data.dday = _calc_dday(ann.deadline)
        result.append(data)
    return result


@router.post("/crawl", tags=["admin"])
async def trigger_crawl(_: object = Depends(get_current_user)):
    asyncio.create_task(_run_crawl())
    return {"status": "crawl triggered"}
