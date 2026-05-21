from datetime import datetime, timedelta, timezone
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.announcement import Announcement
from app.models.filter_config import FilterConfig
from app.schemas.announcement import AnnouncementCreate, AnnouncementFilter
from app.services.notification import notify_new_announcement


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _calc_dday(deadline: datetime | None) -> int | None:
    if not deadline:
        return None
    return (deadline.date() - _now().date()).days


async def upsert_announcements(db: AsyncSession, items: list[dict]) -> tuple[int, int]:
    new_count = 0
    dup_count = 0
    for item in items:
        exists = await db.scalar(
            select(Announcement.id).where(Announcement.bid_number == item["bid_number"])
        )
        if exists:
            dup_count += 1
            continue
        ann = Announcement(**AnnouncementCreate(**item).model_dump())
        db.add(ann)
        new_count += 1
    await db.commit()
    return new_count, dup_count


def _build_conditions(f: AnnouncementFilter) -> list:
    conditions = []
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
    if f.status:
        conditions.append(Announcement.status == f.status)
    if f.deadline_before:
        conditions.append(Announcement.deadline <= f.deadline_before)
    if f.deadline_after:
        conditions.append(Announcement.deadline >= f.deadline_after)
    return conditions


async def get_announcements(db: AsyncSession, f: AnnouncementFilter) -> tuple[list[Announcement], int]:
    conditions = _build_conditions(f)
    where = and_(*conditions) if conditions else True

    total = await db.scalar(select(func.count()).select_from(Announcement).where(where))
    result = await db.execute(
        select(Announcement)
        .where(where)
        .order_by(Announcement.deadline.asc())
        .offset((f.page - 1) * f.size)
        .limit(f.size)
    )
    return list(result.scalars().all()), total or 0


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
