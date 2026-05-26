"""실적 대시보드 집계 — SQL GROUP BY 사용 (메모리 풀스캔 제거)"""
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, case, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bid_application import BidApplication
from app.models.announcement import Announcement

_SUBMITTED = BidApplication.status.in_(("submitted", "won", "lost"))


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def get_summary(db: AsyncSession) -> dict:
    """KPI 요약 카드 — 단일 집계 쿼리"""
    row = (await db.execute(
        select(
            func.count().label("total"),
            func.sum(case((_SUBMITTED, 1), else_=0)).label("submitted"),
            func.sum(case((BidApplication.result == "won", 1), else_=0)).label("won"),
            func.sum(case((BidApplication.result == "lost", 1), else_=0)).label("lost"),
            func.sum(case(
                (BidApplication.result.is_(None) & (BidApplication.status == "submitted"), 1),
                else_=0,
            )).label("pending"),
            func.coalesce(func.sum(case(
                (BidApplication.result == "won", BidApplication.result_price),
                else_=None,
            )), 0).label("award_amount"),
            func.coalesce(func.sum(case(
                (_SUBMITTED, BidApplication.bid_price),
                else_=None,
            )), 0).label("bid_amount"),
        )
    )).one()

    return {
        "total_applications": row.total,
        "submitted": row.submitted,
        "won": row.won,
        "lost": row.lost,
        "pending": row.pending,
        "win_rate": round(row.won / row.submitted * 100, 1) if row.submitted else 0,
        "award_amount": row.award_amount or 0,
        "bid_amount": row.bid_amount or 0,
    }


async def get_monthly_stats(db: AsyncSession, months: int = 12) -> list[dict]:
    """월별 입찰/낙찰 통계 — GROUP BY
    참고: SQLite strftime 사용. PostgreSQL 전환 시 func.to_char(col, 'YYYY-MM') 으로 교체.
    """
    cutoff = _now() - timedelta(days=months * 30)
    month_expr = func.strftime("%Y-%m", BidApplication.submitted_at)

    rows = (await db.execute(
        select(
            month_expr.label("month"),
            func.count().label("submitted"),
            func.sum(case((BidApplication.result == "won", 1), else_=0)).label("won"),
            func.sum(case((BidApplication.result == "lost", 1), else_=0)).label("lost"),
            func.coalesce(func.sum(case(
                (BidApplication.result == "won", BidApplication.result_price),
                else_=None,
            )), 0).label("award_amount"),
        )
        .where(_SUBMITTED, BidApplication.submitted_at >= cutoff)
        .group_by(month_expr)
        .order_by(month_expr)
    )).all()

    return [
        {
            "month": r.month,
            "submitted": r.submitted,
            "won": r.won,
            "lost": r.lost,
            "award_amount": r.award_amount or 0,
            "win_rate": round(r.won / r.submitted * 100, 1) if r.submitted else 0,
        }
        for r in rows
    ]


async def get_by_organization(db: AsyncSession) -> list[dict]:
    """발주처별 실적 — JOIN + GROUP BY (상위 20개)"""
    rows = (await db.execute(
        select(
            func.coalesce(Announcement.organization, "미분류").label("organization"),
            func.count().label("submitted"),
            func.sum(case((BidApplication.result == "won", 1), else_=0)).label("won"),
            func.coalesce(func.sum(case(
                (BidApplication.result == "won", BidApplication.result_price),
                else_=None,
            )), 0).label("award_amount"),
        )
        .join(Announcement, BidApplication.announcement_id == Announcement.id, isouter=True)
        .where(_SUBMITTED)
        .group_by(func.coalesce(Announcement.organization, "미분류"))
        .order_by(func.count().desc())
        .limit(20)
    )).all()

    return [
        {
            "organization": r.organization,
            "submitted": r.submitted,
            "won": r.won,
            "award_amount": r.award_amount or 0,
            "win_rate": round(r.won / r.submitted * 100, 1) if r.submitted else 0,
        }
        for r in rows
    ]


async def get_by_category(db: AsyncSession) -> list[dict]:
    """업종별 실적 — JOIN + GROUP BY"""
    rows = (await db.execute(
        select(
            func.coalesce(Announcement.category, "미분류").label("category"),
            func.count().label("submitted"),
            func.sum(case((BidApplication.result == "won", 1), else_=0)).label("won"),
            func.coalesce(func.sum(case(
                (BidApplication.result == "won", BidApplication.result_price),
                else_=None,
            )), 0).label("award_amount"),
        )
        .join(Announcement, BidApplication.announcement_id == Announcement.id, isouter=True)
        .where(_SUBMITTED)
        .group_by(func.coalesce(Announcement.category, "미분류"))
        .order_by(func.count().desc())
    )).all()

    return [
        {
            "category": r.category,
            "submitted": r.submitted,
            "won": r.won,
            "award_amount": r.award_amount or 0,
            "win_rate": round(r.won / r.submitted * 100, 1) if r.submitted else 0,
        }
        for r in rows
    ]


async def get_loss_analysis(db: AsyncSession) -> list[dict]:
    """유찰 원인 분석 — JOIN으로 2단계 로드 제거"""
    rows = (await db.execute(
        select(
            BidApplication.id,
            BidApplication.announcement_id,
            BidApplication.bid_price,
            BidApplication.winner_price,
            BidApplication.our_rank,
            BidApplication.total_bidders,
            BidApplication.loss_reason,
            BidApplication.submitted_at,
            Announcement.title,
            Announcement.organization,
        )
        .join(Announcement, BidApplication.announcement_id == Announcement.id, isouter=True)
        .where(BidApplication.result == "lost")
        .order_by(BidApplication.submitted_at.desc())
    )).all()

    result = []
    for r in rows:
        price_diff = None
        price_diff_pct = None
        if r.bid_price and r.winner_price:
            price_diff = r.bid_price - r.winner_price
            price_diff_pct = round(price_diff / r.winner_price * 100, 2)
        result.append({
            "id": r.id,
            "title": r.title or f"공고 #{r.announcement_id}",
            "organization": r.organization or "-",
            "our_bid_price": r.bid_price,
            "winner_price": r.winner_price,
            "price_diff": price_diff,
            "price_diff_pct": price_diff_pct,
            "our_rank": r.our_rank,
            "total_bidders": r.total_bidders,
            "loss_reason": r.loss_reason,
            "submitted_at": r.submitted_at,
        })

    return result
