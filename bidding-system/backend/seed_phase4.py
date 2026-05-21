"""Seed Phase 4 test data: announcements, companies, applications with won/lost results."""
import asyncio
import random
from datetime import datetime, timezone, timedelta

from app.core.database import AsyncSessionLocal, init_db
from app.models.announcement import Announcement
from app.models.company import Company
from app.models.bid_application import BidApplication

rng = random.Random(99)

ORGS = ["서울특별시", "경기도청", "인천광역시", "부산광역시", "한국도로공사", "LH공사", "건강보험공단"]
CATS = ["건설공사", "용역", "물품", "IT서비스", "시설관리"]
REGIONS = ["서울", "경기", "인천", "부산", "대전"]


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def seed():
    await init_db()

    async with AsyncSessionLocal() as db:
        # Company
        company = Company(
            name="테스트건설(주)",
            business_number="123-45-67890",
            ceo_name="홍길동",
            address="서울 강남구",
            business_types="건설공사,용역",
            active=True,
        )
        db.add(company)
        await db.flush()

        # Announcements + applications
        for i in range(30):
            base_price = rng.randint(50_000_000, 2_000_000_000)
            org = rng.choice(ORGS)
            cat = rng.choice(CATS)
            region = rng.choice(REGIONS)
            days_ago = rng.randint(30, 365)
            submitted_at = _now() - timedelta(days=days_ago)

            ann = Announcement(
                bid_number=f"202500{1000+i}",
                title=f"{cat} 용역 공고 {i+1}",
                organization=org,
                category=cat,
                region=region,
                budget=base_price * 1.1,
                deadline=submitted_at + timedelta(days=rng.randint(3, 14)),
                source="seed",
                status="closed",
                created_at=submitted_at - timedelta(days=14),
                notified=True,
            )
            db.add(ann)
            await db.flush()

            award_rate = rng.uniform(0.87, 0.98)
            bid_price = round(base_price * award_rate, -3)
            result = "won" if rng.random() < 0.30 else "lost"

            if result == "won":
                result_price = bid_price
                winner_price = None
                our_rank = 1
            else:
                winner_rate = rng.uniform(0.87, 0.97)
                winner_price = round(base_price * winner_rate, -3)
                result_price = None
                our_rank = rng.randint(2, 8)

            total_bidders = rng.randint(our_rank, 12)

            loss_reason = None
            if result == "lost":
                if bid_price and winner_price:
                    diff = (bid_price - winner_price) / winner_price * 100
                    if diff > 0:
                        loss_reason = f"투찰가 낙찰가보다 {diff:.1f}% 높음. 순위 {our_rank}/{total_bidders}위"
                    else:
                        loss_reason = f"투찰가 낙찰가보다 {abs(diff):.1f}% 낮음 (과도한 저가). 순위 {our_rank}/{total_bidders}위"

            app = BidApplication(
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
                result_updated_at=submitted_at + timedelta(days=rng.randint(1, 5)),
                result_notified=True,
            )
            db.add(app)

        await db.commit()
        print("Seeded 30 applications with won/lost results")


asyncio.run(seed())
