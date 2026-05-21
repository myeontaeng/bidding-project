from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.dashboard import (
    get_summary, get_monthly_stats, get_by_organization,
    get_by_category, get_loss_analysis,
)
from app.services.result_tracker import update_result
from app.services.export_service import export_csv, export_excel

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/summary")
async def summary(db: AsyncSession = Depends(get_db)):
    return await get_summary(db)


@router.get("/dashboard/monthly")
async def monthly(months: int = Query(12), db: AsyncSession = Depends(get_db)):
    return await get_monthly_stats(db, months)


@router.get("/dashboard/by-org")
async def by_org(db: AsyncSession = Depends(get_db)):
    return await get_by_organization(db)


@router.get("/dashboard/by-category")
async def by_category(db: AsyncSession = Depends(get_db)):
    return await get_by_category(db)


@router.get("/dashboard/loss-analysis")
async def loss_analysis(db: AsyncSession = Depends(get_db)):
    return await get_loss_analysis(db)


# ── 결과 입력 ─────────────────────────────────────────────────────────────────

class ResultBody:
    pass


from pydantic import BaseModel


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
