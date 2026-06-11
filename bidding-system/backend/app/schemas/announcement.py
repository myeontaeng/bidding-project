from datetime import datetime
from pydantic import BaseModel


class AnnouncementBase(BaseModel):
    bid_number: str
    title: str
    organization: str
    category: str | None = None
    region: str | None = None
    budget: float | None = None
    deadline: datetime | None = None
    published_at: datetime | None = None
    source_url: str | None = None
    source: str = "g2b"
    status: str = "open"
    ministry: str | None = None
    support_type: str | None = None
    budget_available: float | None = None
    eligible_institutions: list | None = None
    description: str | None = None
    opening_date: datetime | None = None


class AnnouncementCreate(AnnouncementBase):
    raw_data: dict | None = None


class AnnouncementRead(AnnouncementBase):
    id: int
    created_at: datetime
    notified: bool
    dday: int | None = None
    fit_score: int | None = None  # 0-100, 활성 필터 기준 적합도

    model_config = {"from_attributes": True}


class AnnouncementFilter(BaseModel):
    keyword: str | None = None
    category: str | None = None
    support_type: str | None = None
    region: str | None = None
    organization: str | None = None
    budget_min: float | None = None
    budget_max: float | None = None
    status: str | None = "open"
    deadline_before: datetime | None = None
    deadline_after: datetime | None = None
    sort_by: str = "deadline"  # deadline | published_at | budget_desc | budget_asc
    page: int = 1
    size: int = 20
