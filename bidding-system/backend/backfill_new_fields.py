"""
기존 announcements raw_data에서 새 필드(ministry, support_type, budget_available,
eligible_institutions) 소급 추출.

실행: python backfill_new_fields.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, init_db
from app.models.announcement import Announcement


def _extract_from_raw(raw: dict) -> dict:
    from app.crawlers.g2b_crawler import _parse_dt

    updates: dict = {}

    ministry = (raw.get("ntceInsttNm") or "").strip()
    if ministry:
        updates["ministry"] = ministry

    support_type = raw.get("bidMethdNm")
    if support_type:
        updates["support_type"] = support_type

    raw_avail = raw.get("asignBdgtAmt")
    if raw_avail:
        try:
            updates["budget_available"] = float(raw_avail)
        except (ValueError, TypeError):
            pass

    prtcpt = raw.get("prtcptLmtYn")
    if prtcpt == "Y":
        updates["eligible_institutions"] = ["제한경쟁"]
    elif prtcpt == "N":
        updates["eligible_institutions"] = ["일반경쟁"]

    opening = _parse_dt(raw.get("opengDt"))
    if opening:
        updates["opening_date"] = opening

    return updates


async def backfill(db: AsyncSession) -> int:
    rows = list(
        (
            await db.execute(
                select(Announcement).where(
                    and_(
                        Announcement.raw_data.isnot(None),
                        Announcement.opening_date.is_(None),
                    )
                )
            )
        )
        .scalars()
        .all()
    )

    updated = 0
    for ann in rows:
        raw = ann.raw_data or {}
        if not isinstance(raw, dict):
            continue
        changes = _extract_from_raw(raw)
        if changes:
            for k, v in changes.items():
                setattr(ann, k, v)
            updated += 1

    if updated:
        await db.commit()
    return updated


async def main():
    await init_db()
    async with AsyncSessionLocal() as db:
        n = await backfill(db)
    print(f"Backfilled {n} announcements")


if __name__ == "__main__":
    asyncio.run(main())
