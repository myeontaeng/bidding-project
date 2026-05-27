import json
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.announcement import Announcement
from app.models.filter_config import FilterConfig
from app.schemas.announcement import AnnouncementCreate, AnnouncementFilter
from app.services.notification import notify_new_announcement


def _now() -> datetime:
    """G2B 마감일은 KST 저장이므로 KST naive datetime 반환."""
    kst = timezone(timedelta(hours=9))
    return datetime.now(kst).replace(tzinfo=None)


def _calc_dday(deadline: datetime | None) -> int | None:
    if not deadline:
        return None
    return (deadline.date() - _now().date()).days


async def upsert_announcements(db: AsyncSession, items: list[dict]) -> tuple[int, int]:
    if not items:
        return 0, 0

    bid_numbers = [item["bid_number"] for item in items]
    existing = set((await db.execute(
        select(Announcement.bid_number).where(Announcement.bid_number.in_(bid_numbers))
    )).scalars().all())

    new_count = 0
    dup_count = 0
    for item in items:
        if item["bid_number"] in existing:
            dup_count += 1
            continue
        ann = Announcement(**AnnouncementCreate(**item).model_dump())
        db.add(ann)
        new_count += 1

    await db.commit()
    return new_count, dup_count


def _build_conditions(f: AnnouncementFilter) -> list:
    conditions = []
    now = _now()

    if f.keyword:
        conditions.append(
            or_(
                Announcement.title.ilike(f"%{f.keyword}%"),
                Announcement.organization.ilike(f"%{f.keyword}%"),
            )
        )
    if f.category:
        conditions.append(Announcement.category == f.category)
    if f.region:
        conditions.append(Announcement.region == f.region)
    if f.organization:
        conditions.append(Announcement.organization.ilike(f"%{f.organization}%"))
    if f.budget_min is not None:
        conditions.append(Announcement.budget >= f.budget_min)
    if f.budget_max is not None:
        conditions.append(Announcement.budget <= f.budget_max)

    # 세분화된 status 필터
    if f.status == "open":
        # 진행중: status=open + (마감일 없거나 아직 안 지남)
        conditions.append(Announcement.status == "open")
        conditions.append(
            or_(Announcement.deadline == None, Announcement.deadline >= now)
        )
    elif f.status == "imminent":
        # 마감임박: 오늘 이후 ~ 7일 이내 마감
        conditions.append(Announcement.status == "open")
        conditions.append(Announcement.deadline >= now)
        conditions.append(Announcement.deadline <= now + timedelta(days=7))
    elif f.status == "no_deadline":
        # 기간정보없음: deadline IS NULL
        conditions.append(Announcement.status == "open")
        conditions.append(Announcement.deadline == None)
    elif f.status == "expired":
        # 마감됨: deadline 지났거나 status=closed
        conditions.append(
            or_(
                Announcement.status == "closed",
                and_(
                    Announcement.status == "open",
                    Announcement.deadline != None,
                    Announcement.deadline < now,
                )
            )
        )
    elif f.status == "closed":
        conditions.append(Announcement.status == "closed")
    # f.status == "" or None → 전체, 조건 없음

    if f.deadline_before:
        conditions.append(Announcement.deadline <= f.deadline_before)
    if f.deadline_after:
        conditions.append(Announcement.deadline >= f.deadline_after)
    return conditions


async def get_announcements(db: AsyncSession, f: AnnouncementFilter) -> tuple[list[Announcement], int]:
    conditions = _build_conditions(f)
    where = and_(*conditions) if conditions else True

    total = await db.scalar(select(func.count()).select_from(Announcement).where(where))
    _sort_map = {
        "published_at": Announcement.published_at.desc(),
        "budget_desc": Announcement.budget.desc(),
        "budget_asc": Announcement.budget.asc(),
    }
    order_clause = _sort_map.get(f.sort_by, Announcement.deadline.asc())

    result = await db.execute(
        select(Announcement)
        .where(where)
        .order_by(order_clause)
        .offset((f.page - 1) * f.size)
        .limit(f.size)
    )
    return list(result.scalars().all()), total or 0


async def backfill_deadlines(db: AsyncSession) -> int:
    """raw_data에서 bidClseDt를 읽어 NULL deadline 소급 복구."""
    from app.crawlers.g2b_crawler import _parse_dt
    rows = list((await db.execute(
        select(Announcement).where(
            and_(Announcement.deadline == None, Announcement.raw_data != None)
        )
    )).scalars().all())

    updated = 0
    for ann in rows:
        raw = ann.raw_data or {}
        close_str = raw.get("bidClseDt") or raw.get("opengDt") or raw.get("bidBeginDt")
        if close_str:
            parsed = _parse_dt(str(close_str))
            if parsed:
                ann.deadline = parsed
                updated += 1

    if updated:
        await db.commit()
    return updated


async def close_expired_announcements(db: AsyncSession) -> int:
    """deadline 지난 open 공고를 closed 로 전환."""
    result = await db.execute(
        update(Announcement)
        .where(
            and_(
                Announcement.status == "open",
                Announcement.deadline != None,
                Announcement.deadline < _now(),
            )
        )
        .values(status="closed")
    )
    await db.commit()
    return result.rowcount or 0


async def notify_new_announcements(db: AsyncSession):
    new_anns = list((await db.execute(
        select(Announcement).where(Announcement.notified == False)
    )).scalars().all())
    if not new_anns:
        return

    filters = list((await db.execute(
        select(FilterConfig).where(FilterConfig.active == True)
    )).scalars().all())

    for ann in new_anns:
        for fc in filters:
            if _matches_filter(ann, fc):
                await notify_new_announcement(
                    {
                        "bid_number": ann.bid_number,
                        "title": ann.title,
                        "organization": ann.organization,
                        "budget": ann.budget,
                        "deadline": ann.deadline,
                        "source_url": ann.source_url,
                        "dday": _calc_dday(ann.deadline),
                    },
                    email=fc.notify_email,
                    slack=fc.notify_slack,
                )
                break
        ann.notified = True
    await db.commit()


def _matches_filter(ann: Announcement, fc: FilterConfig) -> bool:
    if fc.keywords:
        if not any(kw.lower() in ann.title.lower() for kw in fc.keywords):
            return False
    if fc.categories and ann.category:
        if ann.category not in fc.categories:
            return False
    if fc.regions and ann.region:
        if ann.region not in fc.regions:
            return False
    if fc.organizations:
        if not any(org.lower() in ann.organization.lower() for org in fc.organizations):
            return False
    if fc.budget_min is not None and ann.budget is not None:
        if ann.budget < fc.budget_min:
            return False
    if fc.budget_max is not None and ann.budget is not None:
        if ann.budget > fc.budget_max:
            return False
    return True


async def send_dday_reminders(db: AsyncSession):
    filters = list((await db.execute(
        select(FilterConfig).where(FilterConfig.active == True)
    )).scalars().all())

    for fc in filters:
        for d in (fc.reminder_days or [7, 3, 1]):
            target = _now().date() + timedelta(days=d)
            anns = list((await db.execute(
                select(Announcement).where(
                    and_(
                        Announcement.deadline >= datetime.combine(target, datetime.min.time()),
                        Announcement.deadline < datetime.combine(target + timedelta(days=1), datetime.min.time()),
                        Announcement.status == "open",
                    )
                )
            )).scalars().all())

            for ann in anns:
                if not _matches_filter(ann, fc):
                    continue
                sent = ann.reminders_sent or []
                if d in sent:
                    continue
                await notify_new_announcement(
                    {
                        "bid_number": ann.bid_number,
                        "title": ann.title,
                        "organization": ann.organization,
                        "budget": ann.budget,
                        "deadline": ann.deadline,
                        "source_url": ann.source_url,
                        "dday": d,
                    },
                    email=fc.notify_email,
                    slack=fc.notify_slack,
                )
                ann.reminders_sent = sent + [d]
    await db.commit()
