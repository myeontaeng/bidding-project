"""대시보드 초기 데모 데이터 — 앱이 없을 때만 실행"""
import random
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.announcement import Announcement
from app.models.company import Company
from app.models.bid_application import BidApplication

_ORGS = ["서울특별시", "경기도청", "인천광역시", "부산광역시", "한국도로공사", "LH공사", "건강보험공단"]
_CATS = ["건설공사", "용역", "물품", "IT서비스", "시설관리"]
_REGIONS = ["서울", "경기", "인천", "부산", "대전"]
_RNG = random.Random(99)


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def seed_demo_data(db: AsyncSession) -> int:
    """애플리케이션 데이터 없을 때 데모 데이터 30건 생성."""
    existing = await db.scalar(select(func.count()).select_from(BidApplication))
    if existing:
        return 0

    company = Company(
        name="데모건설(주)",
        business_number="123-45-67890",
        ceo_name="홍길동",
        address="서울 강남구",
        business_types=",".join(_CATS[:3]),
        active=True,
    )
    db.add(company)
    await db.flush()

    count = 0
    for i in range(30):
        base_price = _RNG.randint(50_000_000, 2_000_000_000)
        org = _RNG.choice(_ORGS)
        cat = _RNG.choice(_CATS)
        region = _RNG.choice(_REGIONS)
        days_ago = _RNG.randint(30, 365)
        submitted_at = _now() - timedelta(days=days_ago)

        ann = Announcement(
            bid_number=f"DEMO{2025_0000 + i:08d}",
            title=f"{org} {cat} 사업 {i + 1}",
            organization=org,
            category=cat,
            region=region,
            budget=round(base_price * 1.1, -3),
            deadline=submitted_at + timedelta(days=_RNG.randint(3, 14)),
            source="demo",
            status="closed",
            created_at=submitted_at - timedelta(days=14),
            notified=True,
        )
        db.add(ann)
        await db.flush()

        award_rate = _RNG.uniform(0.87, 0.98)
        bid_price = round(base_price * award_rate, -3)
        result = "won" if _RNG.random() < 0.30 else "lost"

        if result == "won":
            result_price = bid_price
            winner_price = None
            our_rank = 1
        else:
            winner_price = round(base_price * _RNG.uniform(0.87, 0.97), -3)
            result_price = None
            our_rank = _RNG.randint(2, 8)

        total_bidders = _RNG.randint(our_rank, 12)

        loss_reason = None
        if result == "lost" and bid_price and winner_price:
            diff = (bid_price - winner_price) / winner_price * 100
            loss_reason = (
                f"투찰가 낙찰가보다 {diff:.1f}% 높음. 순위 {our_rank}/{total_bidders}위"
                if diff > 0
                else f"투찰가 낙찰가보다 {abs(diff):.1f}% 낮음 (과도한 저가). 순위 {our_rank}/{total_bidders}위"
            )

        db.add(BidApplication(
            announcement_id=ann.id,
            company_id=company.id,
            status=result,
            bid_price=bid_price,
            submitted_at=submitted_at,
            created_at=submitted_at - timedelta(hours=2),
            result=result,
            result_price=result_price,
            winner_price=winner_price,
            our_rank=our_rank,
            total_bidders=total_bidders,
            loss_reason=loss_reason,
            result_updated_at=submitted_at + timedelta(days=_RNG.randint(1, 5)),
            result_notified=True,
        ))
        count += 1

    await db.commit()
    return count
