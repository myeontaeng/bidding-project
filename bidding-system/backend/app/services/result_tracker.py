"""입찰 결과 추적 + 알림"""
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bid_application import BidApplication
from app.models.announcement import Announcement
from app.services.notification import send_slack, send_email

logger = logging.getLogger(__name__)


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def update_result(
    db: AsyncSession,
    app_id: int,
    result: str,               # won / lost
    result_price: float | None = None,
    winner_price: float | None = None,
    our_rank: int | None = None,
    total_bidders: int | None = None,
) -> BidApplication:
    """결과 수동 업데이트 + 알림"""
    app = await db.get(BidApplication, app_id)
    if not app:
        from fastapi import HTTPException
        raise HTTPException(404, "Application not found")

    app.result = result
    app.result_price = result_price
    app.winner_price = winner_price
    app.our_rank = our_rank
    app.total_bidders = total_bidders
    app.result_updated_at = _now()
    app.status = result  # won / lost

    # 유찰 원인 자동 분석
    if result == "lost":
        app.loss_reason = _analyze_loss(
            bid_price=app.bid_price,
            winner_price=winner_price,
            our_rank=our_rank,
            total_bidders=total_bidders,
        )

    await db.commit()
    await db.refresh(app)

    # 알림 (미발송 건만)
    if not app.result_notified:
        await _notify_result(db, app)
        app.result_notified = True
        await db.commit()

    return app


def _analyze_loss(
    bid_price: float | None,
    winner_price: float | None,
    our_rank: int | None,
    total_bidders: int | None,
) -> str:
    parts = []
    if bid_price and winner_price:
        diff_pct = (bid_price - winner_price) / winner_price * 100
        if diff_pct > 0:
            parts.append(f"투찰가 낙찰가보다 {diff_pct:.1f}% 높음")
        else:
            parts.append(f"투찰가 낙찰가보다 {abs(diff_pct):.1f}% 낮음 (과도한 저가)")
    if our_rank and total_bidders:
        parts.append(f"순위 {our_rank}/{total_bidders}위")
    return ". ".join(parts) if parts else "원인 미입력"


async def _notify_result(db: AsyncSession, app: BidApplication):
    ann = await db.get(Announcement, app.announcement_id)
    title = ann.title if ann else f"공고 #{app.announcement_id}"
    emoji = "🎉" if app.result == "won" else "❌"
    status_kr = "낙찰" if app.result == "won" else "유찰"

    msg_lines = [
        f"{emoji} [{status_kr}] {title}",
        f"• 투찰가: {app.bid_price:,.0f}원" if app.bid_price else "",
    ]
    if app.result == "won" and app.result_price:
        msg_lines.append(f"• 낙찰가: {app.result_price:,.0f}원")
    if app.result == "lost":
        if app.winner_price:
            msg_lines.append(f"• 낙찰가(1위): {app.winner_price:,.0f}원")
        if app.loss_reason:
            msg_lines.append(f"• 원인: {app.loss_reason}")

    message = "\n".join(l for l in msg_lines if l)
    await send_slack(message)


async def poll_submitted_results(db: AsyncSession):
    """
    제출 완료 건 중 결과 미확인 건 폴링.
    실제 나라장터 크롤링 대신 수동 업데이트 안내 로그.
    """
    pending = list((await db.execute(
        select(BidApplication).where(
            BidApplication.status == "submitted",
            BidApplication.result.is_(None),
        )
    )).scalars().all())

    if pending:
        logger.info(
            "결과 미확인 입찰 건 %d건 — 나라장터에서 확인 후 /api/v1/applications/{id}/result 로 업데이트",
            len(pending),
        )
