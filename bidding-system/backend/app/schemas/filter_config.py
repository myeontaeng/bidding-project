from pydantic import BaseModel


class FilterConfigCreate(BaseModel):
    name: str
    keywords: list[str] | None = None
    categories: list[str] | None = None
    regions: list[str] | None = None
    organizations: list[str] | None = None
    budget_min: float | None = None
    budget_max: float | None = None
    notify_email: str | None = None
    notify_slack: bool = False
    reminder_days: list[int] = [7, 3, 1]
    active: bool = True


class FilterConfigRead(FilterConfigCreate):
    id: int

    model_config = {"from_attributes": True}
