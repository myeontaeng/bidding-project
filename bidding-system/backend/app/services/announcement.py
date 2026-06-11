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


async def get_announcement(db: AsyncSession, ann_id: int) -> Announcement | None:
    result = await db.execute(select(Announcement).where(Announcement.id == ann_id))
    return result.scalar_one_or_none()


def compute_match(ann: Announcement, company) -> dict:
    """회사 프로필과 공고 조건 매칭 점수 계산."""
    checks = []

    # 업종 일치
    biz_types = [b.strip().lower() for b in (company.business_types or "").split(",") if b.strip()]
    cat = (ann.category or "").lower()
    sup = (ann.support_type or "").lower()
    title_lower = ann.title.lower()
    biz_match = any(
        bt in cat or bt in sup or bt in title_lower or cat in bt or sup in bt
        for bt in biz_types
    ) if biz_types else None
    checks.append({
        "label": "업종 일치",
        "pass": bool(biz_match),
        "unknown": biz_types == [],
        "detail": ann.category or ann.support_type or "-",
    })

    # 지역 적합
    region = ann.region or ""
    if not region or region == "전국":
        region_ok, region_detail = True, "지역 제한 없음"
    else:
        addr = (company.address or "").lower()
        region_ok = region.lower() in addr
        region_detail = f"{region} 필요"
    checks.append({"label": "지역 적합", "pass": region_ok, "unknown": False, "detail": region_detail})

    # 참가 자격
    eligible = ann.eligible_institutions or []
    is_open = not eligible or "일반경쟁" in eligible
    checks.append({
        "label": "참가 자격",
        "pass": is_open,
        "unknown": False,
        "detail": ", ".join(eligible) if eligible else "일반경쟁",
    })

    # 예산 정보 존재 여부
    has_budget = ann.budget is not None
    fmt_budget = f"{ann.budget:,.0f}원" if ann.budget is not None else "정보 없음"
    checks.append({"label": "예산 정보", "pass": has_budget, "unknown": not has_budget, "detail": fmt_budget})

    passed = sum(1 for c in checks if c["pass"] and not c.get("unknown"))
    total = sum(1 for c in checks if not c.get("unknown"))
    score = round(passed / total * 100) if total else 0

    return {"score": score, "checks": checks, "company_name": company.name}


async def generate_summary(ann: Announcement) -> str:
    """공고 요약 생성. OpenAI 키 있으면 AI, 없으면 템플릿."""
    from app.core.config import settings

    if settings.OPENAI_API_KEY:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            budget_line = f"예산: {ann.budget:,.0f}원" if ann.budget else "예산: 정보 없음"
            prompt = (
                f"다음 입찰 공고를 3-4문장으로 요약해주세요. 핵심 목적, 지원 조건, 예산을 포함해주세요.\n\n"
                f"공고명: {ann.title}\n"
                f"발주처: {ann.organization}\n"
                f"공고기관: {ann.ministry or '-'}\n"
                f"입찰방법: {ann.support_type or '-'}\n"
                f"{budget_line}"
            )
            resp = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "공공조달 입찰 공고 요약 전문가입니다. 간결하고 핵심적인 한국어 요약을 제공합니다."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=300,
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            pass

    # 템플릿 기반 요약
    budget_str = f"{ann.budget:,.0f}원" if ann.budget else "정보 없음"
    lines = [
        f"이 공고는 {ann.organization}에서 발주한 사업입니다.",
    ]
    if ann.ministry and ann.ministry != ann.organization:
        lines.append(f"공고기관은 {ann.ministry}입니다.")
    if ann.support_type:
        lines.append(f"입찰 방법은 {ann.support_type}이며, 예산은 {budget_str}입니다.")
    else:
        lines.append(f"예산은 {budget_str}입니다.")
    if ann.category:
        lines.append(f"업종 분류: {ann.category}.")
    if ann.eligible_institutions:
        lines.append(f"참가 자격: {', '.join(ann.eligible_institutions)}.")
    return " ".join(lines)


async def compute_bid_score(db: AsyncSession, ann: Announcement) -> dict:
    """공고에 대한 입찰 가부 종합 판단 점수 (0-100)."""
    from app.models.bid_application import BidApplication
    from app.models.award_record import AwardRecord
    from sqlalchemy import select, func, case

    breakdown = {}
    reasons = []

    # 1. 예산 매력도 (25pt) — 예산 있고 적정 규모면 높은 점수
    budget_score = 0
    if ann.budget is None:
        budget_score = 10
        reasons.append("예산 정보 없음 — 확인 필요")
    elif ann.budget < 10_000_000:
        budget_score = 10
        reasons.append(f"소규모 공고 (예산 {ann.budget/1e6:.0f}백만원)")
    elif ann.budget < 5_000_000_000:
        budget_score = 25
        reasons.append(f"적정 예산 규모 ({ann.budget/1e8:.1f}억원)")
    else:
        budget_score = 15
        reasons.append(f"대형 공고 — 자격 요건 확인 필요 ({ann.budget/1e8:.0f}억원)")
    breakdown["budget"] = {"score": budget_score, "max": 25, "label": "예산 매력도"}

    # 2. 마감 여유 (20pt) — D-day 기준
    deadline_score = 0
    dday = _calc_dday(ann.deadline)
    if dday is None:
        deadline_score = 10
        reasons.append("마감일 정보 없음")
    elif dday < 0:
        deadline_score = 0
        reasons.append("마감 지남")
    elif dday <= 3:
        deadline_score = 5
        reasons.append(f"마감 임박 (D-{dday})")
    elif dday <= 7:
        deadline_score = 12
        reasons.append(f"마감 {dday}일 남음")
    else:
        deadline_score = 20
        reasons.append(f"충분한 준비 기간 (D-{dday})")
    breakdown["deadline"] = {"score": deadline_score, "max": 20, "label": "마감 여유"}

    # 3. 경쟁 강도 (25pt) — AwardRecord의 bid_count 기반
    rows = (await db.execute(
        select(func.avg(AwardRecord.bid_count).label("avg_bidders"))
        .where(AwardRecord.category == ann.category)
        .where(AwardRecord.bid_count.isnot(None))
    )).one()
    avg_bidders = rows.avg_bidders or 8
    if avg_bidders <= 5:
        comp_score = 25
        reasons.append(f"낮은 경쟁 강도 (평균 {avg_bidders:.0f}개사)")
    elif avg_bidders <= 10:
        comp_score = 18
        reasons.append(f"보통 경쟁 강도 (평균 {avg_bidders:.0f}개사)")
    elif avg_bidders <= 20:
        comp_score = 10
        reasons.append(f"높은 경쟁 강도 (평균 {avg_bidders:.0f}개사)")
    else:
        comp_score = 5
        reasons.append(f"매우 높은 경쟁 강도 (평균 {avg_bidders:.0f}개사)")
    breakdown["competition"] = {"score": comp_score, "max": 25, "label": "경쟁 강도"}

    # 4. 낙찰 이력 (30pt) — 같은 발주처/업종 대상 우리 win rate
    history = (await db.execute(
        select(
            func.count().label("total"),
            func.sum(case((BidApplication.result == "won", 1), else_=0)).label("won"),
        )
        .join(__import__("app.models.announcement", fromlist=["Announcement"]).Announcement,
              BidApplication.announcement_id == __import__("app.models.announcement", fromlist=["Announcement"]).Announcement.id,
              isouter=True)
        .where(BidApplication.status.in_(["submitted", "won", "lost"]))
    )).one()

    if not history.total:
        hist_score = 15  # 이력 없으면 중간값
        reasons.append("입찰 이력 없음 — 첫 도전")
    else:
        win_rate = history.won / history.total
        hist_score = int(win_rate * 30)
        reasons.append(f"전체 낙찰률 {win_rate*100:.0f}% ({history.won}/{history.total}건)")
    breakdown["win_history"] = {"score": hist_score, "max": 30, "label": "낙찰 이력"}

    overall = sum(v["score"] for v in breakdown.values())
    if overall >= 65:
        recommendation = "bid"
        rec_label = "입찰 권장"
        rec_color = "green"
    elif overall >= 40:
        recommendation = "caution"
        rec_label = "신중 검토"
        rec_color = "yellow"
    else:
        recommendation = "pass"
        rec_label = "입찰 보류"
        rec_color = "red"

    # 전문가 검토 플래그: 50억 이상 or 신중검토+5억 이상
    needs_expert = bool(
        (ann.budget and ann.budget >= 5_000_000_000) or
        (recommendation == "caution" and ann.budget and ann.budget >= 500_000_000)
    )
    expert_reason: str | None = None
    if ann.budget and ann.budget >= 5_000_000_000:
        expert_reason = f"대형 공고 ({ann.budget/1e8:.0f}억원) — 담당자 검토 권장"
    elif needs_expert:
        expert_reason = f"신중 검토 구간 ({ann.budget/1e8:.1f}억원) — 전문가 의견 확인 권장"

    return {
        "overall": overall,
        "max": 100,
        "recommendation": recommendation,
        "recommendation_label": rec_label,
        "recommendation_color": rec_color,
        "breakdown": breakdown,
        "reasoning": reasons,
        "needs_expert_review": needs_expert,
        "expert_review_reason": expert_reason,
    }


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
    if f.support_type:
        conditions.append(Announcement.support_type == f.support_type)
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


def compute_fit_score(ann: Announcement, filters: list[FilterConfig]) -> int | None:
    """활성 필터 목록 대비 공고 적합도 점수 (0-100). 필터 없으면 None."""
    if not filters:
        return None

    best = 0
    for fc in filters:
        score = 0
        # 키워드 매칭 (35pt)
        if fc.keywords:
            title_low = ann.title.lower()
            matched = sum(1 for kw in fc.keywords if kw.lower() in title_low)
            score += int(35 * matched / len(fc.keywords))
        else:
            score += 35

        # 카테고리 매칭 (25pt)
        if fc.categories:
            score += 25 if ann.category in fc.categories else 0
        else:
            score += 25

        # 지역 매칭 (20pt)
        if fc.regions:
            score += 20 if (not ann.region or ann.region == "전국" or ann.region in fc.regions) else 0
        else:
            score += 20

        # 예산 범위 (15pt)
        if ann.budget is not None:
            lo_ok = fc.budget_min is None or ann.budget >= fc.budget_min
            hi_ok = fc.budget_max is None or ann.budget <= fc.budget_max
            score += 15 if (lo_ok and hi_ok) else 0
        else:
            score += 8  # 예산 정보 없음 → 절반

        # 발주처 매칭 (5pt)
        if fc.organizations:
            score += 5 if any(o.lower() in ann.organization.lower() for o in fc.organizations) else 0
        else:
            score += 5

        best = max(best, score)

    return min(100, best)


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


_BID_METHODS = {"전자입찰", "직찰", "전자시담", "수의계약", "제한경쟁입찰", "일반경쟁입찰", "지명경쟁입찰"}


async def backfill_category(db: AsyncSession) -> int:
    """category가 입찰방법으로 저장된 기존 데이터 → 업종으로 재분류.
    support_type이 NULL인 경우도 함께 보정."""
    from app.crawlers.g2b_crawler import _classify_category

    rows = list((await db.execute(
        select(Announcement).where(
            or_(
                Announcement.category.in_(_BID_METHODS),
                Announcement.category.is_(None),
            )
        )
    )).scalars().all())

    updated = 0
    for ann in rows:
        raw = ann.raw_data or {}
        bid_method = raw.get("bidMethdNm") or ann.support_type or ann.category

        # support_type 보정
        if ann.support_type is None and bid_method in _BID_METHODS:
            ann.support_type = bid_method

        # category → 업종으로 재분류
        ann.category = _classify_category(ann.title or "")
        updated += 1

    if updated:
        await db.commit()
    return updated


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
