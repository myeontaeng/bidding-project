"""공공데이터포털 낙찰 이력 수집 + 시드 데이터 생성"""
import logging
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

import httpx

from app.models.award_record import AwardRecord
from app.core.config import settings

logger = logging.getLogger(__name__)

# 낙찰 결과 API (공공데이터포털 나라장터 낙찰정보)
AWARD_API = "https://apis.data.go.kr/1230000/AwardPublicInfoService01/getAwardResultListInfo01"

CATEGORIES = ["IT서비스", "소프트웨어", "건설", "용역", "물품구매", "시설공사"]
ORGS = ["서울시청", "경기도청", "행정안전부", "교육부", "국토교통부", "기획재정부",
        "환경부", "보건복지부", "과학기술정보통신부", "국방부"]
REGIONS = ["서울", "경기", "부산", "인천", "대구", "광주", "대전", "울산", "세종"]


async def fetch_from_public_api(
    service_key: str, page: int = 1, num_rows: int = 100
) -> list[dict]:
    """공공데이터포털 낙찰 결과 API 호출 (1페이지)"""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.get(
                AWARD_API,
                params={
                    "serviceKey": service_key,
                    "numOfRows": num_rows,
                    "pageNo": page,
                    "type": "json",
                },
            )
            res.raise_for_status()
            data = res.json()
            items = data.get("response", {}).get("body", {}).get("items", [])
            return items if isinstance(items, list) else ([items] if items else [])
    except Exception as e:
        logger.error("Public API fetch failed: %s", e)
        return []


def _map_api_item(item: dict) -> dict | None:
    """공공데이터 낙찰 결과 응답 → AwardRecord dict"""
    bid_number = item.get("bidNtceNo") or item.get("bid_ntce_no")
    if not bid_number:
        return None

    def _to_float(v) -> float | None:
        try:
            return float(str(v).replace(",", "")) if v else None
        except (ValueError, TypeError):
            return None

    base_price = _to_float(item.get("presmptPrce") or item.get("asignBdgtAmt"))
    award_price = _to_float(item.get("sucsfbidAmt") or item.get("bidAmt"))
    award_rate = round(award_price / base_price, 4) if base_price and award_price and base_price > 0 else None

    award_date: datetime | None = None
    for field in ("opengDate", "bidClseDatetime", "sucsfbidDt"):
        raw = item.get(field, "")
        for fmt in ("%Y%m%d%H%M", "%Y/%m/%d %H:%M", "%Y-%m-%d", "%Y%m%d"):
            try:
                award_date = datetime.strptime(str(raw)[:len(fmt)], fmt)
                break
            except (ValueError, TypeError):
                continue
        if award_date:
            break

    return {
        "bid_number": str(bid_number),
        "title": item.get("bidNtceNm") or "제목 미상",
        "organization": item.get("ntceInsttNm") or item.get("dminsttNm") or "미상",
        "category": item.get("bidMethtNm") or None,
        "region": None,
        "base_price": base_price,
        "award_price": award_price,
        "award_rate": award_rate,
        "bid_count": int(item.get("sucsfbidCnt") or 0) or None,
        "awarded_company": item.get("sucsfbidCorpNm") or None,
        "award_date": award_date or datetime.now(timezone.utc).replace(tzinfo=None),
        "source": "g2b_api",
        "raw_data": item,
    }


async def _fetch_all_pages(service_key: str, pages: int = 5) -> list[dict]:
    """여러 페이지 순차 수집 — 빈 페이지 만나면 중단"""
    results = []
    for page in range(1, pages + 1):
        items = await fetch_from_public_api(service_key, page=page)
        if not items:
            break
        results.extend(items)
    return results


def _generate_seed_records(count: int = 500) -> list[dict]:
    """공공API 키 없을 때 통계적으로 유사한 시드 데이터 생성"""
    records = []
    rng = random.Random(42)

    # 실제 낙찰률 분포: 87~94% 구간에 집중 (정규분포 근사)
    for i in range(count):
        base = rng.uniform(10_000_000, 500_000_000)
        rate = max(0.80, min(0.99, rng.gauss(0.905, 0.025)))  # 평균 90.5%, σ=2.5%
        award = base * rate
        days_ago = rng.randint(0, 365 * 3)
        cat = rng.choice(CATEGORIES)
        records.append({
            "bid_number": f"SEED{2024000 + i:06d}",
            "title": f"{rng.choice(ORGS)} {cat} 구축 사업",
            "organization": rng.choice(ORGS),
            "category": cat,
            "region": rng.choice(REGIONS),
            "base_price": round(base, -3),
            "award_price": round(award, -3),
            "award_rate": round(rate, 4),
            "bid_count": rng.randint(3, 20),
            "awarded_company": f"(주)테스트업체{rng.randint(1, 50)}",
            "award_date": datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days_ago),
            "source": "seed",
        })
    return records


async def collect_award_records(db: AsyncSession) -> int:
    """낙찰 이력 수집 - G2B_API_KEY 있으면 공공데이터, 없으면 시드 데이터"""
    if settings.G2B_API_KEY:
        raw_items = await _fetch_all_pages(settings.G2B_API_KEY)
        records = [r for item in raw_items if (r := _map_api_item(item))]
        if not records:
            logger.warning("G2B API returned no usable records, falling back to seed data")
            records = _generate_seed_records(500)
        source_label = "g2b_api"
    else:
        existing_count = await db.scalar(select(func.count()).select_from(AwardRecord))
        if existing_count and existing_count >= 100:
            logger.info("Award records already exist (%d), skip seed", existing_count)
            return 0
        records = _generate_seed_records(500)
        source_label = "seed"

    # 배치 중복 체크 (N+1 제거)
    bid_numbers = [r["bid_number"] for r in records]
    existing_bid_numbers = set((await db.execute(
        select(AwardRecord.bid_number).where(AwardRecord.bid_number.in_(bid_numbers))
    )).scalars().all())

    new_count = 0
    for r in records:
        if r["bid_number"] not in existing_bid_numbers:
            db.add(AwardRecord(**r))
            new_count += 1

    await db.commit()
    logger.info("Collected %d new award records (source=%s)", new_count, source_label)
    return new_count


async def get_award_stats(db: AsyncSession, category: str | None = None) -> dict:
    """낙찰률 분포 통계"""
    stmt = select(AwardRecord).where(AwardRecord.award_rate.isnot(None))
    if category:
        stmt = stmt.where(AwardRecord.category == category)

    result = await db.execute(stmt)
    records = result.scalars().all()

    if not records:
        return {"count": 0}

    rates = [r.award_rate for r in records]
    rates.sort()
    n = len(rates)

    buckets: dict[str, int] = {}
    for r in rates:
        key = f"{int(r * 100)}-{int(r * 100) + 1}%"
        buckets[key] = buckets.get(key, 0) + 1

    return {
        "count": n,
        "mean": round(sum(rates) / n, 4),
        "median": round(rates[n // 2], 4),
        "p10": round(rates[int(n * 0.10)], 4),
        "p25": round(rates[int(n * 0.25)], 4),
        "p75": round(rates[int(n * 0.75)], 4),
        "p90": round(rates[int(n * 0.90)], 4),
        "min": round(min(rates), 4),
        "max": round(max(rates), 4),
        "distribution": buckets,
        "category": category,
    }
