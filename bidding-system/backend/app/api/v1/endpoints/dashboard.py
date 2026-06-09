from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.services.dashboard import (
    get_summary, get_monthly_stats, get_by_organization,
    get_by_category, get_loss_analysis, get_today_overview, get_org_analysis,
    get_archive_stats, get_curated_collections,
)
from app.services.result_tracker import update_result
from app.services.export_service import export_csv, export_excel

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/today")
async def today_overview(db: AsyncSession = Depends(get_db)):
    """공개 — 오늘/이번 주 현황 요약 (인증 불필요)"""
    return await get_today_overview(db)


@router.get("/dashboard/archive-stats")
async def archive_stats(db: AsyncSession = Depends(get_db)):
    """공개 — 아카이브 지표 (인증 불필요)"""
    return await get_archive_stats(db)


@router.get("/dashboard/collections")
async def curated_collections(db: AsyncSession = Depends(get_db)):
    """공개 — 큐레이션 컬렉션 3종 (인증 불필요)"""
    return await get_curated_collections(db)


@router.get("/dashboard/summary", dependencies=[Depends(get_current_user)])
async def summary(db: AsyncSession = Depends(get_db)):
    return await get_summary(db)


@router.get("/dashboard/monthly", dependencies=[Depends(get_current_user)])
async def monthly(months: int = Query(12), db: AsyncSession = Depends(get_db)):
    return await get_monthly_stats(db, months)


@router.get("/dashboard/by-org", dependencies=[Depends(get_current_user)])
async def by_org(db: AsyncSession = Depends(get_db)):
    return await get_by_organization(db)


@router.get("/dashboard/by-category", dependencies=[Depends(get_current_user)])
async def by_category(db: AsyncSession = Depends(get_db)):
    return await get_by_category(db)


@router.get("/dashboard/loss-analysis", dependencies=[Depends(get_current_user)])
async def loss_analysis(db: AsyncSession = Depends(get_db)):
    return await get_loss_analysis(db)


@router.get("/dashboard/org-analysis", dependencies=[Depends(get_current_user)])
async def org_analysis(organization: str = Query(...), db: AsyncSession = Depends(get_db)):
    return await get_org_analysis(db, organization)


# ── 감사 로그 ─────────────────────────────────────────────────────────────────

@router.get("/audit", dependencies=[Depends(get_current_user)])
async def audit_trail(
    entity_type: str = Query(...),
    entity_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    from app.services.audit import get_audit_trail
    logs = await get_audit_trail(db, entity_type, entity_id)
    return [
        {"id": l.id, "action": l.action, "actor": l.actor,
         "details": l.details, "created_at": l.created_at}
        for l in logs
    ]


# ── 결과 입력 ─────────────────────────────────────────────────────────────────

class ResultUpdate(BaseModel):
    result: str                        # won / lost
    result_price: float | None = None
    winner_price: float | None = None
    our_rank: int | None = None
    total_bidders: int | None = None


@router.post("/applications/{app_id}/result")
async def update_application_result(
    app_id: int,
    body: ResultUpdate,
    db: AsyncSession = Depends(get_db),
):
    app = await update_result(
        db, app_id,
        result=body.result,
        result_price=body.result_price,
        winner_price=body.winner_price,
        our_rank=body.our_rank,
        total_bidders=body.total_bidders,
    )
    return {
        "id": app.id,
        "result": app.result,
        "loss_reason": app.loss_reason,
        "result_updated_at": app.result_updated_at,
    }


# ── 내보내기 ──────────────────────────────────────────────────────────────────

@router.get("/export/csv")
async def download_csv(db: AsyncSession = Depends(get_db)):
    data = await export_csv(db)
    return Response(
        content=data,
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": "attachment; filename=bidding_results.csv"},
    )


@router.get("/export/excel")
async def download_excel(db: AsyncSession = Depends(get_db)):
    data = await export_excel(db)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=bidding_results.xlsx"},
    )
