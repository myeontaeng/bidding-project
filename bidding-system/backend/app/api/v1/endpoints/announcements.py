import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.schemas.announcement import AnnouncementFilter, AnnouncementRead
from app.services.announcement import (
    get_announcements, get_announcement, _calc_dday,
    compute_match, compute_fit_score, compute_bid_score, generate_summary,
)
from app.services.scheduler import _run_crawl

router = APIRouter(prefix="/announcements", tags=["announcements"])


@router.get("", response_model=list[AnnouncementRead])
async def list_announcements(
    response: Response,
    keyword: str | None = Query(None),
    category: str | None = Query(None),
    support_type: str | None = Query(None),
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
        keyword=keyword, category=category, support_type=support_type,
        region=region, organization=organization,
        budget_min=budget_min, budget_max=budget_max,
        status=status, page=page, size=size,
        deadline_before=_parse_date(deadline_before, end_of_day=True),
        deadline_after=_parse_date(deadline_after),
        sort_by=sort_by,
    )
    anns, total = await get_announcements(db, f)
    response.headers["X-Total-Count"] = str(total)

    # 활성 필터 로드 (적합도 점수 계산용)
    from app.models.filter_config import FilterConfig
    from sqlalchemy import select as _select
    active_filters = list((await db.execute(
        _select(FilterConfig).where(FilterConfig.active == True)
    )).scalars().all())

    result = []
    for ann in anns:
        data = AnnouncementRead.model_validate(ann)
        data.dday = _calc_dday(ann.deadline)
        data.fit_score = compute_fit_score(ann, active_filters)
        result.append(data)
    return result


@router.get("/{ann_id}", response_model=AnnouncementRead)
async def get_announcement_detail(
    ann_id: int,
    db: AsyncSession = Depends(get_db),
):
    ann = await get_announcement(db, ann_id)
    if not ann:
        raise HTTPException(status_code=404, detail="Announcement not found")
    data = AnnouncementRead.model_validate(ann)
    data.dday = _calc_dday(ann.deadline)
    return data


@router.get("/{ann_id}/match")
async def match_announcement(
    ann_id: int,
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    ann = await get_announcement(db, ann_id)
    if not ann:
        raise HTTPException(status_code=404, detail="Announcement not found")
    from app.services.company import get_company_raw
    company = await get_company_raw(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return compute_match(ann, company)


@router.post("/{ann_id}/summarize")
async def summarize_announcement(
    ann_id: int,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(get_current_user),
):
    ann = await get_announcement(db, ann_id)
    if not ann:
        raise HTTPException(status_code=404, detail="Announcement not found")
    summary = await generate_summary(ann)
    ann.description = summary
    await db.commit()
    return {"description": summary}


@router.get("/{ann_id}/bid-score")
async def bid_score(
    ann_id: int,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(get_current_user),
):
    ann = await get_announcement(db, ann_id)
    if not ann:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return await compute_bid_score(db, ann)


@router.get("/{ann_id}/audit")
async def announcement_audit(
    ann_id: int,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(get_current_user),
):
    from app.services.audit import get_audit_trail
    logs = await get_audit_trail(db, "application", ann_id)
    return [
        {"id": l.id, "action": l.action, "actor": l.actor,
         "details": l.details, "created_at": l.created_at}
        for l in logs
    ]


@router.get("/{ann_id}/auto-setup")
async def auto_setup(
    ann_id: int,
    company_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """원클릭 자동 분석: bid_score + 요약 + 가격 추천 + 필요 서류 + 회사 매칭"""
    ann = await get_announcement(db, ann_id)
    if not ann:
        raise HTTPException(status_code=404, detail="Announcement not found")

    bid_score, summary = await asyncio.gather(
        compute_bid_score(db, ann),
        generate_summary(ann),
    )

    price_rec = None
    if ann.budget:
        from app.services.price_model import predict_award_rate
        price_rec = await predict_award_rate(db, ann.budget, ann.category, ann.region)

    from app.services.document_ai import identify_required_docs
    required_docs = await identify_required_docs(ann.title, ann.title)

    match = None
    if company_id:
        from app.services.company import get_company_raw
        company = await get_company_raw(db, company_id)
        if company:
            match = compute_match(ann, company)

    return {
        "announcement_id": ann_id,
        "title": ann.title,
        "summary": summary,
        "bid_score": bid_score,
        "price_recommendation": price_rec,
        "required_docs": required_docs,
        "match": match,
    }


@router.post("/crawl", tags=["admin"])
async def trigger_crawl(_: object = Depends(get_current_user)):
    asyncio.create_task(_run_crawl())
    return {"status": "crawl triggered"}
