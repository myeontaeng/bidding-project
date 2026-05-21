"""실적 대시보드 집계"""
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bid_application import BidApplication
from app.models.announcement import Announcement


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def get_summary(db: AsyncSession) -> dict:
    """KPI 요약 카드"""
    apps = list((await db.execute(select(BidApplication))).scalars().all())
    submitted = [a for a in apps if a.status in ("submitted", "won", "lost")]
    won = [a for a in apps if a.result == "won"]
    lost = [a for a in apps if a.result == "lost"]

    award_amount = sum(a.result_price for a in won if a.result_price)
    bid_amount = sum(a.bid_price for a in submitted if a.bid_price)

    win_rate = round(len(won) / len(submitted) * 100, 1) if submitted else 0

    return {
        "total_applications": len(apps),
        "submitted": len(submitted),
        "won": len(won),
        "lost": len(lost),
        "pending": len([a for a in apps if a.result is None and a.status == "submitted"]),
        "win_rate": win_rate,
        "award_amount": award_amount,
        "bid_amount": bid_amount,
    }


async def get_monthly_stats(db: AsyncSession, months: int = 12) -> list[dict]:
    """월별 입찰 건수 / 낙찰 건수 / 수주 금액"""
    apps = list((await db.execute(
        select(BidApplication).where(BidApplication.status.in_(("submitted", "won", "lost")))
    )).scalars().all())

    bucket: dict[str, dict] = defaultdict(lambda: {"month": "", "submitted": 0, "won": 0, "lost": 0, "award_amount": 0.0})

    cutoff = _now() - timedelta(days=months * 30)
    for a in apps:
        dt = a.submitted_at or a.created_at
        if dt < cutoff:
            continue
        key = dt.strftime("%Y-%m")
        bucket[key]["month"] = key
        bucket[key]["submitted"] += 1
        if a.result == "won":
            bucket[key]["won"] += 1
            bucket[key]["award_amount"] += a.result_price or 0
        elif a.result == "lost":
            bucket[key]["lost"] += 1

    result = sorted(bucket.values(), key=lambda x: x["month"])
    for r in result:
        r["win_rate"] = round(r["won"] / r["submitted"] * 100, 1) if r["submitted"] else 0
    return result


async def get_by_organization(db: AsyncSession) -> list[dict]:
    """발주처별 실적"""
    apps = list((await db.execute(
        select(BidApplication).where(BidApplication.status.in_(("submitted", "won", "lost")))
    )).scalars().all())

    # announcement 정보 조인
    ann_ids = list({a.announcement_id for a in apps})
    anns = {a.id: a for a in (await db.execute(
        select(Announcement).where(Announcement.id.in_(ann_ids))
    )).scalars().all()}

    bucket: dict[str, dict] = defaultdict(lambda: {"organization": "", "submitted": 0, "won": 0, "award_amount": 0.0})
    for a in apps:
        ann = anns.get(a.announcement_id)
        org = ann.organization if ann else "미분류"
        bucket[org]["organization"] = org
        bucket[org]["submitted"] += 1
        if a.result == "won":
            bucket[org]["won"] += 1
            bucket[org]["award_amount"] += a.result_price or 0

    result = sorted(bucket.values(), key=lambda x: x["submitted"], reverse=True)
    for r in result:
        r["win_rate"] = round(r["won"] / r["submitted"] * 100, 1) if r["submitted"] else 0
    return result[:20]


async def get_by_category(db: AsyncSession) -> list[dict]:
    """업종별 실적"""
    apps = list((await db.execute(
        select(BidApplication).where(BidApplication.status.in_(("submitted", "won", "lost")))
    )).scalars().all())

    ann_ids = list({a.announcement_id for a in apps})
    anns = {a.id: a for a in (await db.execute(
        select(Announcement).where(Announcement.id.in_(ann_ids))
    )).scalars().all()}

    bucket: dict[str, dict] = defaultdict(lambda: {"category": "", "submitted": 0, "won": 0, "award_amount": 0.0})
    for a in apps:
        ann = anns.get(a.announcement_id)
        cat = (ann.category if ann else None) or "미분류"
        bucket[cat]["category"] = cat
        bucket[cat]["submitted"] += 1
        if a.result == "won":
            bucket[cat]["won"] += 1
            bucket[cat]["award_amount"] += a.result_price or 0

    result = sorted(bucket.values(), key=lambda x: x["submitted"], reverse=True)
    for r in result:
        r["win_rate"] = round(r["won"] / r["submitted"] * 100, 1) if r["submitted"] else 0
    return result


async def get_loss_analysis(db: AsyncSession) -> list[dict]:
    """유찰 원인 분석"""
    lost_apps = list((await db.execute(
        select(BidApplication).where(BidApplication.result == "lost")
    )).scalars().all())

    ann_ids = list({a.announcement_id for a in lost_apps})
    anns = {a.id: a for a in (await db.execute(
        select(Announcement).where(Announcement.id.in_(ann_ids))
    )).scalars().all()}

    result = []
    for a in lost_apps:
        ann = anns.get(a.announcement_id)
        price_diff = None
        price_diff_pct = None
        if a.bid_price and a.winner_price:
            price_diff = a.bid_price - a.winner_price
            price_diff_pct = round(price_diff / a.winner_price * 100, 2)

        result.append({
            "id": a.id,
            "title": ann.title if ann else f"공고 #{a.announcement_id}",
            "organization": ann.organization if ann else "-",
            "our_bid_price": a.bid_price,
            "winner_price": a.winner_price,
            "price_diff": price_diff,
            "price_diff_pct": price_diff_pct,
            "our_rank": a.our_rank,
            "total_bidders": a.total_bidders,
            "loss_reason": a.loss_reason,
            "submitted_at": a.submitted_at,
        })

    return sorted(result, key=lambda x: x["submitted_at"] or datetime.min, reverse=True)
