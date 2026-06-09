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


async def get_org_analysis(db: AsyncSession, organization: str) -> dict:
    """특정 발주처 과거 공고 + 우리 입찰 이력 분석."""
    from app.models.announcement import Announcement
    from sqlalchemy import and_

    # 발주처 공고 통계
    org_rows = (await db.execute(
        select(
            func.count().label("total_announcements"),
            func.avg(Announcement.budget).label("avg_budget"),
            func.max(Announcement.budget).label("max_budget"),
            func.min(Announcement.budget).label("min_budget"),
        )
        .where(Announcement.organization.ilike(f"%{organization}%"))
    )).one()

    # 업종 분포
    cat_rows = (await db.execute(
        select(Announcement.category, func.count().label("cnt"))
        .where(Announcement.organization.ilike(f"%{organization}%"))
        .where(Announcement.category.isnot(None))
        .group_by(Announcement.category)
        .order_by(func.count().desc())
        .limit(5)
    )).all()

    # 우리 입찰 이력
    bid_rows = (await db.execute(
        select(
            func.count().label("total"),
            func.sum(case((BidApplication.result == "won", 1), else_=0)).label("won"),
            func.coalesce(func.sum(case(
                (BidApplication.result == "won", BidApplication.result_price), else_=None
            )), 0).label("award_amount"),
        )
        .join(Announcement, BidApplication.announcement_id == Announcement.id, isouter=True)
        .where(_SUBMITTED)
        .where(Announcement.organization.ilike(f"%{organization}%"))
    )).one()

    return {
        "organization": organization,
        "total_announcements": org_rows.total_announcements or 0,
        "avg_budget": round(org_rows.avg_budget) if org_rows.avg_budget else None,
        "max_budget": org_rows.max_budget,
        "min_budget": org_rows.min_budget,
        "top_categories": [{"category": r.category, "count": r.cnt} for r in cat_rows],
        "our_bids": bid_rows.total or 0,
        "our_wins": bid_rows.won or 0,
        "our_win_rate": round(bid_rows.won / bid_rows.total * 100, 1) if bid_rows.total else 0,
        "our_award_amount": bid_rows.award_amount or 0,
    }


async def get_today_overview(db: AsyncSession) -> dict:
    """공고 목록 상단 현황 바 — 인증 불필요 (공개 데이터만)"""
    from app.models.announcement import Announcement
    from sqlalchemy import and_, or_
    now = _now()
    week_later = now + timedelta(days=7)
    today_end = now.replace(hour=23, minute=59, second=59)

    # 이번 주 마감 공고 수
    closing_week = await db.scalar(
        select(func.count()).select_from(Announcement).where(
            and_(
                Announcement.status == "open",
                Announcement.deadline >= now,
                Announcement.deadline <= week_later,
            )
        )
    )

    # 오늘 마감
    closing_today = await db.scalar(
        select(func.count()).select_from(Announcement).where(
            and_(
                Announcement.status == "open",
                Announcement.deadline >= now,
                Announcement.deadline <= today_end,
            )
        )
    )

    # 진행중 입찰(결과 미입력)
    pending = await db.scalar(
        select(func.count()).select_from(BidApplication).where(
            BidApplication.status == "submitted",
            BidApplication.result.is_(None),
        )
    )

    # 전체 공개 공고 수
    total_open = await db.scalar(
        select(func.count()).select_from(Announcement).where(
            and_(
                Announcement.status == "open",
                or_(Announcement.deadline.is_(None), Announcement.deadline >= now),
            )
        )
    )

    return {
        "total_open": total_open or 0,
        "closing_today": closing_today or 0,
        "closing_this_week": closing_week or 0,
        "pending_applications": pending or 0,
    }


async def get_archive_stats(db: AsyncSession) -> dict:
    """아카이브 지표 — 공개 홈 상단 노출용"""
    from app.models.award_record import AwardRecord
    from app.models.filter_config import FilterConfig

    total_ann = await db.scalar(select(func.count()).select_from(Announcement))
    total_awards = await db.scalar(select(func.count()).select_from(AwardRecord))
    avg_rate = await db.scalar(
        select(func.avg(AwardRecord.award_rate)).where(AwardRecord.award_rate.isnot(None))
    )
    bid_row = (await db.execute(
        select(
            func.count().label("submitted"),
            func.sum(case((BidApplication.result == "won", 1), else_=0)).label("won"),
        ).where(_SUBMITTED)
    )).one()
    active_filters = await db.scalar(
        select(func.count()).select_from(FilterConfig).where(FilterConfig.active == True)
    )
    return {
        "total_announcements": total_ann or 0,
        "total_award_records": total_awards or 0,
        "avg_award_rate": round(avg_rate * 100, 1) if avg_rate else None,
        "our_win_rate": round(bid_row.won / bid_row.submitted * 100, 1) if bid_row.submitted else None,
        "our_total_bids": bid_row.submitted or 0,
        "active_filters": active_filters or 0,
    }


async def get_curated_collections(db: AsyncSession) -> list[dict]:
    """큐레이션 컬렉션 3종 — 오늘의 유망 / 마감임박 / 소규모"""
    from sqlalchemy import and_, or_
    now = _now()
    week_later = now + timedelta(days=7)

    def _ann_dict(ann: Announcement) -> dict:
        from app.services.announcement import _calc_dday
        return {
            "id": ann.id,
            "title": ann.title,
            "organization": ann.organization,
            "budget": ann.budget,
            "deadline": ann.deadline.isoformat() if ann.deadline else None,
            "category": ann.category,
            "dday": _calc_dday(ann.deadline),
            "source_url": ann.source_url,
        }

    # 오늘의 유망: 적정 예산(1억~50억) + D-8 이상 여유
    promising = list((await db.execute(
        select(Announcement).where(and_(
            Announcement.status == "open",
            Announcement.deadline > week_later,
            Announcement.budget >= 100_000_000,
            Announcement.budget <= 5_000_000_000,
        )).order_by(Announcement.published_at.desc()).limit(5)
    )).scalars().all())

    # 마감임박: 이번 주 마감
    imminent = list((await db.execute(
        select(Announcement).where(and_(
            Announcement.status == "open",
            Announcement.deadline >= now,
            Announcement.deadline <= week_later,
        )).order_by(Announcement.deadline.asc()).limit(5)
    )).scalars().all())

    # 소규모: 3억 미만
    small = list((await db.execute(
        select(Announcement).where(and_(
            Announcement.status == "open",
            Announcement.budget.isnot(None),
            Announcement.budget > 0,
            Announcement.budget < 300_000_000,
            or_(Announcement.deadline.is_(None), Announcement.deadline >= now),
        )).order_by(Announcement.published_at.desc()).limit(5)
    )).scalars().all())

    return [
        {
            "key": "promising",
            "label": "오늘의 유망 공고",
            "description": "적정 예산 + D-8 이상 여유",
            "icon": "✨",
            "items": [_ann_dict(a) for a in promising],
        },
        {
            "key": "imminent",
            "label": "마감임박 공고",
            "description": "이번 주 마감 — 지금 바로 검토",
            "icon": "⏰",
            "items": [_ann_dict(a) for a in imminent],
        },
        {
            "key": "small_scale",
            "label": "소규모 공고",
            "description": "3억 미만 — 낮은 진입장벽",
            "icon": "🎯",
            "items": [_ann_dict(a) for a in small],
        },
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
