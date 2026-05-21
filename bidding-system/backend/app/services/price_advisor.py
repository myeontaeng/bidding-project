"""시나리오 시뮬레이션 + 마진율 분석"""
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.award_record import AwardRecord


async def simulate_scenarios(
    db: AsyncSession,
    base_price: float,
    category: str | None,
    cost: float | None = None,
) -> dict:
    """
    입찰가 시나리오별 낙찰 확률 계산.
    과거 낙찰 이력의 누적 분포 함수(CDF)에서 확률 추정.
    """
    stmt = select(AwardRecord.award_rate).where(AwardRecord.award_rate.isnot(None))
    if category:
        stmt = stmt.where(AwardRecord.category == category)

    rates = [r[0] for r in (await db.execute(stmt)).all()]

    if len(rates) < 10:
        rates = _default_rates()

    rates_arr = np.array(rates)

    # 80% ~ 99% 구간을 0.5% 단위로 시뮬레이션
    scenarios = []
    for rate_pct in range(800, 995, 5):
        rate = rate_pct / 1000
        bid_price = round(base_price * rate, -3)
        # 이 가격 이하로 낙찰된 이력 비율 = 낙찰 확률
        win_prob = float(np.mean(rates_arr <= rate))
        margin_rate = None
        margin_amount = None
        if cost is not None and cost > 0:
            margin_amount = bid_price - cost
            margin_rate = round(margin_amount / bid_price * 100, 2)

        scenarios.append({
            "rate": round(rate, 3),
            "rate_pct": f"{rate * 100:.1f}%",
            "bid_price": bid_price,
            "win_prob": round(win_prob, 3),
            "win_prob_pct": f"{win_prob * 100:.1f}%",
            "margin_rate": margin_rate,
            "margin_amount": round(margin_amount, -3) if margin_amount is not None else None,
        })

    # 최적점: 기대값(낙찰확률 × 마진) 최대화
    if cost is not None:
        best = max(
            (s for s in scenarios if s["margin_amount"] and s["margin_amount"] > 0),
            key=lambda s: s["win_prob"] * s["margin_amount"],
            default=scenarios[len(scenarios) // 2],
        )
    else:
        # 낙찰확률 40~70% 구간에서 중간값 선택
        candidates = [s for s in scenarios if 0.40 <= s["win_prob"] <= 0.70]
        best = candidates[len(candidates) // 2] if candidates else scenarios[len(scenarios) // 2]

    return {
        "scenarios": scenarios,
        "optimal": best,
        "data_count": len(rates),
        "category": category,
    }


async def calc_margin(
    base_price: float,
    bid_price: float,
    cost: float,
    overhead_rate: float = 0.10,
) -> dict:
    """원가 대비 마진율 계산"""
    total_cost = cost * (1 + overhead_rate)
    margin = bid_price - total_cost
    margin_rate = margin / bid_price * 100
    award_rate = bid_price / base_price * 100

    return {
        "base_price": base_price,
        "bid_price": bid_price,
        "direct_cost": cost,
        "overhead": round(cost * overhead_rate, -3),
        "total_cost": round(total_cost, -3),
        "margin": round(margin, -3),
        "margin_rate": round(margin_rate, 2),
        "award_rate": round(award_rate, 2),
        "is_profitable": margin > 0,
    }


def _default_rates() -> list[float]:
    """통계 기반 기본 낙찰률 분포 (실제 데이터 없을 때)"""
    rng = np.random.default_rng(42)
    return list(np.clip(rng.normal(0.905, 0.025, 200), 0.80, 0.99))
