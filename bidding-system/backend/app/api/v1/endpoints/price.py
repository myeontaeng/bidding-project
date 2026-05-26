from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.award_record import AwardRecord, PriceModel
from app.services.award_collector import collect_award_records, get_award_stats
from app.services.price_model import train_model, predict_award_rate
from app.services.price_advisor import simulate_scenarios, calc_margin

router = APIRouter(prefix="/price", tags=["price"])


@router.post("/collect", tags=["admin"])
async def trigger_collect(db: AsyncSession = Depends(get_db), _: object = Depends(get_current_user)):
    """낙찰 이력 수집 (공공데이터 or 시드 데이터)"""
    count = await collect_award_records(db)
    return {"collected": count}


@router.get("/awards")
async def list_awards(
    category: str | None = Query(None),
    organization: str | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AwardRecord).order_by(desc(AwardRecord.award_date)).limit(limit)
    if category:
        stmt = stmt.where(AwardRecord.category == category)
    if organization:
        stmt = stmt.where(AwardRecord.organization.ilike(f"%{organization}%"))
    result = await db.execute(stmt)
    records = result.scalars().all()
    return [
        {
            "id": r.id,
            "bid_number": r.bid_number,
            "title": r.title,
            "organization": r.organization,
            "category": r.category,
            "base_price": r.base_price,
            "award_price": r.award_price,
            "award_rate": r.award_rate,
            "bid_count": r.bid_count,
            "award_date": r.award_date,
        }
        for r in records
    ]


@router.get("/stats")
async def award_stats(
    category: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """낙찰률 분포 통계"""
    return await get_award_stats(db, category)


@router.post("/train", tags=["admin"])
async def trigger_train(
    category: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """모델 학습 트리거"""
    return await train_model(db, category)


@router.get("/models")
async def list_models(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PriceModel).order_by(desc(PriceModel.trained_at)).limit(10)
    )
    return [
        {
            "id": m.id,
            "version": m.version,
            "category": m.category,
            "train_count": m.train_count,
            "mae": m.mae,
            "active": m.active,
            "trained_at": m.trained_at,
        }
        for m in result.scalars().all()
    ]


@router.get("/recommend")
async def recommend(
    base_price: float = Query(..., description="예정가격"),
    category: str | None = Query(None),
    region: str | None = Query(None),
    bid_count: int = Query(8, description="예상 투찰 참가 업체 수"),
    db: AsyncSession = Depends(get_db),
):
    """ML 기반 최적 투찰가 범위 추천"""
    return await predict_award_rate(db, base_price, category, region, bid_count)


@router.get("/simulate")
async def simulate(
    base_price: float = Query(...),
    category: str | None = Query(None),
    cost: float | None = Query(None, description="직접 원가 (마진 계산용)"),
    db: AsyncSession = Depends(get_db),
):
    """시나리오별 낙찰 확률 시뮬레이션"""
    return await simulate_scenarios(db, base_price, category, cost)


@router.get("/margin")
async def margin(
    base_price: float = Query(...),
    bid_price: float = Query(...),
    cost: float = Query(...),
    overhead_rate: float = Query(0.10, description="간접비 비율"),
):
    """원가 대비 마진율 계산"""
    return await calc_margin(base_price, bid_price, cost, overhead_rate)
